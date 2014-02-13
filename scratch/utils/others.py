# coding: utf-8

from wtforms import BooleanField
import jsonpickle

pickler = jsonpickle.pickler.Pickler(unpicklable=False, max_depth=2)

def flatten(model):
    """去除pickler.flatten里面的一个字段"""
    json = pickler.flatten(model)
    json.pop('_sa_instance_state', None)
    return json


def form_to_dict(form):
    form_dict = {}

    for key in form._fields:  # 可以编写一个更好的函数，可惜我不会。。。
        if isinstance(form._fields[key].data, BooleanField) or isinstance(form._fields[key].data, int):
            form_dict[key] = form._fields[key].data
            continue

        if form._fields[key].data:
            form_dict[key] = form._fields[key].data

    return form_dict


#取得一个正确的返回字典
class success_dic(object):
    def __init__(self):
        self.dic = {}
        self.dic['code'] = 200
        self.dic['message'] = 'success'
        #self.dic['test'] = 'test success'

    def set(self, k, v):
        self.dic[k] = v