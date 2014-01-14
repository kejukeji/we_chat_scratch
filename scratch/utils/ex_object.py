# coding: utf-8


def delete_attrs(obj, attr_list):
    """批量删除属性"""
    for attr in attr_list:
        delattr(obj, attr)