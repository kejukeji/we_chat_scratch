# coding: UTF-8
from flask_restful import reqparse
from flask.ext import restful
from scratch.services.to_login import get_user_format, get_user_by_id_format,get_user_by_name_format
from scratch.utils.others import success_dic

class UserRestful(restful.Resource):
    ''''''
    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=str, required=False, help=u'user_id required')

        args = parser.parse_args()

        user_id = args.get('user_id', '1')

        success = success_dic().dic
        get_user_by_id_format(user_id, success)
        return success


class UserByNameRestful(restful.Resource):
    ''''''
    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument('user_name',type=str,required=True,help=u'name is required')
        args = parser.parse_args()

        user_name = args.get('user_name','sjm')
        success = success_dic().dic
        get_user_by_name_format(user_name, success)
        return success

