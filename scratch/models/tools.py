# coding: utf-8


def get_one(model, lookup_id):
    """查找一个元素，通过ID"""
    return model.query.filter(model.id == lookup_id).first()