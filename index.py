import configparser
import logging
import os
from collections import defaultdict
from datetime import datetime
from multiprocessing import Lock

from flask import Flask, request
from pymongo import MongoClient, ReturnDocument, UpdateMany
from pymongo.database import Database
from pymongo.errors import PyMongoError
from pymongo.results import InsertOneResult, BulkWriteResult
from werkzeug.exceptions import BadRequest

from data_validator import DataValidator
from exception_handler import handle_exceptions

logger = logging.getLogger(__name__)


def make_app(db: Database, data_validator: DataValidator) -> Flask:
    app = Flask(__name__)

    locks = defaultdict(Lock)

    @app.route('/imports', methods=['POST'])
    @handle_exceptions(logger)
    def imports():
        """
        Принимает на вход набор с данными о жителях в формате json
        и сохраняет его с уникальным идентификатором import_id.

        :raises: :class:`BadRequest`: Content-Type в заголовке запроса не равен application/json
        :raises: :class:`PyMongoError`: Операция записи в базу данных не была разрешена

        :returns: В случае успеха возвращается ответ с идентификатором импорта
        :rtype: flask.Response
        """
        if not request.is_json:
            raise BadRequest('Content-Type must be application/json')

        import_data = request.get_json()
        data_validator.validate_import(import_data)
        for citizen in import_data['citizens']:
            citizen['birth_date'] = datetime.strptime(citizen['birth_date'], '%d.%m.%Y')

        with locks['post_imports']:
            import_id = db['imports'].count()
            import_data['import_id'] = import_id

            db_response: InsertOneResult = db['imports'].insert_one(import_data)
            if db_response.acknowledged:
                response = {'data': {'import_id': import_id}}
                return response, 201
            else:
                raise PyMongoError('Operation was not acknowledged')

    @app.route('/imports/<int:import_id>/citizens/<int:citizen_id>', methods=['PATCH'])
    @handle_exceptions(logger)
    def citizen(import_id: int, citizen_id: int):
        """
        Изменяет информацию о жителе в указанном наборе данных.
        На вход подается JSON в котором можно указать любые данные о жителе.

        :param int import_id: Уникальный идентификатор поставки, в которой изменяется информация о жителе
        :param int citizen_id: Уникальный индентификатор жителя в поставке
        :raises: :class:`BadRequest`: Content-Type в заголовке запроса не равен application/json
        :raises: :class:`PyMongoError`: Объект с указанным уникальным идентификатором не был найден в базе данных

        :return: Актуальная информация об указанном жителе
        :rtype: flask.Response
        """

        def make_update_relative_request(operation: str, relative_ids: list):
            return UpdateMany({'import_id': import_id},
                              {operation: {'citizens.$[element].relatives': citizen_id}},
                              array_filters=[{'element.citizen_id': {'$in': relative_ids}}])

        if not request.is_json:
            raise BadRequest('Content-Type must be application/json')

        patch_data = request.get_json()
        data_validator.validate_citizen_patch(citizen_id, patch_data)
        if 'birth_date' in patch_data:
            patch_data['birth_date'] = datetime.strptime(patch_data['birth_date'], '%d.%m.%Y')

        with locks[str(import_id)]:
            if 'relatives' in patch_data:
                old_relatives_response: dict = db['imports'].find_one({'import_id': import_id},
                                                                      {'citizens': {
                                                                          '$elemMatch': {
                                                                              'citizen_id': citizen_id}}})
                if old_relatives_response is None:
                    raise PyMongoError('Import or citizen with specified id not found')
                old_relatives = set(old_relatives_response['citizens'][0]['relatives'])
                new_relatives = set(patch_data['relatives'])
                to_push = new_relatives - old_relatives
                to_pull = old_relatives - new_relatives
                db_requests = []
                if to_push:
                    db_requests.append(make_update_relative_request('$push', list(to_push)))
                if to_pull:
                    db_requests.append(make_update_relative_request('$pull', list(to_pull)))
                if db_requests:
                    bulk_response: BulkWriteResult = db['imports'].bulk_write(db_requests)
                    if bulk_response.modified_count != len(db_requests):
                        raise PyMongoError('Relative with specified id not found')

            update_data = {
                '$set': {f'citizens.$.{key}': val for key, val in patch_data.items()}
            }
            projection = {
                '_id': 0,
                'import_id': 0,
                'citizens': {
                    '$elemMatch': {'citizen_id': citizen_id}
                }
            }
            db_response: dict = db['imports'].find_one_and_update(
                filter={'import_id': import_id, 'citizens.citizen_id': citizen_id}, update=update_data,
                projection=projection, return_document=ReturnDocument.AFTER)
            if db_response is None:
                raise PyMongoError('Import or citizen with specified id not found')
            return {'data': db_response['citizens'][0]}, 201

    @app.route('/imports/<int:import_id>/citizens', methods=['GET'])
    @handle_exceptions(logger)
    def citizens(import_id: int):
        """
        Возвращает список всех жителей для указанного набора данных.

        :param int import_id: Уникальный идентификатор поставки
        :raises: :class:`PyMongoError`: Объект с указанным уникальным идентификатором не был найден в базе данных

        :return: Список жителей в указанной поставке
        :rtype: flask.Response
        """
        with locks[str(import_id)]:
            import_data = db['imports'].find_one({'import_id': import_id}, {'_id': 0, 'import_id': 0})
            if import_data is None:
                raise PyMongoError('Import with specified id not found')
            for citizen in import_data['citizens']:
                citizen['birth_date'] = citizen['birth_date'].strftime('%d.%m.%Y')
            return {'data': import_data['citizens']}, 201

    return app


def main():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.cfg')
    config.read(config_path)
    db_uri = config['DATABASE']['DATABASE_URI']
    db_name = config['DATABASE']['DATABASE_NAME']

    db = MongoClient(db_uri)[db_name]
    data_validator = DataValidator()
    app = make_app(db, data_validator)
    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
