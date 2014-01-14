# coding: utf-8

"""后台添加用户的视图"""
import logging

from flask.ext.admin.contrib.sqla import ModelView
from flask import flash
from flask.ext.admin.babel import gettext
from sqlalchemy import or_
from flask.ext.admin.base import expose
from sqlalchemy.orm import joinedload
from flask.ext.admin.contrib.sqla import tools
from flask.ext import login
from flask import request, url_for, redirect
from flask.ext.admin.form import get_form_opts
from flask.ext.admin.helpers import validate_form_on_submit
from flask.ext.admin.model.helpers import get_mdict_item_or_list

from ..models.admin_user import AdminUser
from ..models.user import User
from ..utils.others import form_to_dict
from ..utils.ex_object import delete_attrs


class SuperUserView(ModelView):
    """后台添加超级管理员的类"""

    page_size = 30
    form_choices = dict(
        admin=[('1111', u'猫吧管理员')]
    )
    pub_user_filter = '1111'  # 过滤用户的标志

    def __init__(self, db, **kwargs):
        ModelView.__init__(self, AdminUser, db, **kwargs)

    def scaffold_form(self):
        """改写form"""
        form_class = super(SuperUserView, self).scaffold_form()
        delete_attrs(form_class, ['pub', 'sign_up_date'])

        return form_class

    def create_model(self, form):
        try:
            if not bool(str(form.password.data)):
                flash(u'密码不能为空', 'error')
                return False
            if not self._valid_form(form):
                flash(u'用户名重复', 'error')
                return False
            model = self.model(**form_to_dict(form))
            self.session.add(model)
            self.session.commit()
        except Exception, ex:
            flash(gettext('Failed to create model. %(error)s', error=str(ex)), 'error')
            logging.exception('Failed to create model')
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, True)

        return True

    def update_model(self, form, model):
        try:
            if not self._valid_form(form, model=model):
                flash(u'用户名重复', 'error')
                return False
            model.update(**form_to_dict(form))
            self.session.commit()
        except Exception, ex:
            flash(gettext('Failed to update model. %(error)s', error=str(ex)), 'error')
            logging.exception('Failed to update model')
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def get_list(self, page, sort_column, sort_desc, search, filters, execute=True, admin=None):
        """
        得到过滤的视图
        """

        # Will contain names of joined tables to avoid duplicate joins
        joins = set()

        query = self.get_query()
        count_query = self.get_count_query()

        if admin is not None:
            query = query.filter(AdminUser.admin == admin)

        # Apply search criteria
        if self._search_supported and search:
            # Apply search-related joins
            if self._search_joins:
                for jn in self._search_joins.values():
                    query = query.join(jn)
                    count_query = count_query.join(jn)

                joins = set(self._search_joins.keys())

            # Apply terms
            terms = search.split(' ')

            for term in terms:
                if not term:
                    continue

                stmt = tools.parse_like_term(term)
                filter_stmt = [c.ilike(stmt) for c in self._search_fields]
                query = query.filter(or_(*filter_stmt))
                count_query = count_query.filter(or_(*filter_stmt))

        # Apply filters
        if filters and self._filters:
            for idx, value in filters:
                flt = self._filters[idx]

                # Figure out joins
                tbl = flt.column.table.name

                join_tables = self._filter_joins.get(tbl, [])

                for table in join_tables:
                    if table.name not in joins:
                        query = query.join(table)
                        count_query = count_query.join(table)
                        joins.add(table.name)

                # Apply filter
                query = flt.apply(query, value)
                count_query = flt.apply(count_query, value)

        # Calculate number of rows
        count = count_query.scalar()

        # Auto join
        for j in self._auto_joins:
            query = query.options(joinedload(j))

        # Sorting
        if sort_column is not None:
            if sort_column in self._sortable_columns:
                sort_field = self._sortable_columns[sort_column]

                query, joins = self._order_by(query, joins, sort_field, sort_desc)
        else:
            order = self._get_default_order()

            if order:
                query, joins = self._order_by(query, joins, order[0], order[1])

        # Pagination
        if page is not None:
            query = query.offset(page * self.page_size)

        query = query.limit(self.page_size)

        # Execute if needed
        if execute:
            query = query.all()

        return count, query

    @expose('/')
    def index_view(self):
        """
            List view
        """
        # Grab parameters from URL
        page, sort_idx, sort_desc, search, filters = self._get_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(sort_idx)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get count and data
        count, data = self.get_list(page, sort_column, sort_desc,
                                    search, filters, admin=self.pub_user_filter)

        # Calculate number of pages
        num_pages = count // self.page_size
        if count % self.page_size != 0:
            num_pages += 1

        # Pregenerate filters
        if self._filters:
            filters_data = dict()

            for idx, f in enumerate(self._filters):
                flt_data = f.get_options(self)

                if flt_data:
                    filters_data[idx] = flt_data
        else:
            filters_data = None

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_url('.index_view', p, sort_idx, sort_desc,
                                 search, filters)

        def sort_url(column, invert=False):
            desc = None

            if invert and not sort_desc:
                desc = 1

            return self._get_url('.index_view', page, column, desc,
                                 search, filters)

        # Actions
        actions, actions_confirmation = self.get_actions_list()

        return self.render(self.list_template,
                               data=data,
                               # List
                               list_columns=self._list_columns,
                               sortable_columns=self._sortable_columns,
                               # Stuff
                               enumerate=enumerate,
                               get_pk_value=self.get_pk_value,
                               get_value=self.get_list_value,
                               return_url=self._get_url('.index_view',
                                                        page,
                                                        sort_idx,
                                                        sort_desc,
                                                        search,
                                                        filters),
                               # Pagination
                               count=count,
                               pager_url=pager_url,
                               num_pages=num_pages,
                               page=page,
                               # Sorting
                               sort_column=sort_idx,
                               sort_desc=sort_desc,
                               sort_url=sort_url,
                               # Search
                               search_supported=self._search_supported,
                               clear_search_url=self._get_url('.index_view',
                                                              None,
                                                              sort_idx,
                                                              sort_desc),
                               search=search,
                               # Filters
                               filters=self._filters,
                               filter_groups=self._filter_groups,
                               filter_types=self._filter_types,
                               filter_data=filters_data,
                               active_filters=filters,

                               # Actions
                               actions=actions,
                               actions_confirmation=actions_confirmation)

    def _valid_form(self, form, model=None):
        """检查form，放置用户名重复问题，添加猫吧超级管理员
        """
        form_dic = form_to_dict(form)
        if model is None:
            return not self._has_user(form_dic['name'])
        else:
            if str(model.name) == form_dic['name']:
                return True
            return not self._has_user(form_dic['name'])

    def _has_user(self, name):
        """存在返回True，不存在返回False"""
        return bool(AdminUser.query.filter(AdminUser.name == name).count())

    def is_accessible(self):
        return login.current_user.is_normal_superuser()


class ManagerUserView(SuperUserView):
    """酒吧管理员的类"""

    form_choices = dict(
        admin=[('111', u'酒吧管理员')]
    )
    can_create = False
    can_delete = False
    pub_user_filter = '111'

    def __init__(self, db, **kwargs):
        ModelView.__init__(self, AdminUser, db, **kwargs)


class UserView(ModelView):
    """酒吧会员管理"""

    can_create = False
    can_delete = True
    can_edit = True
    column_labels = {
        "id": u'卡号',
        "mobile": u'手机',
        "sign_up_date": u'注册时间',
        "open_id": u'微信',
        "card_date": u'注册时间',
        "card_money": u'金额',
        "card_credit": u'积分',
        "card_status": u'状态',
        "name": u'姓名'
    }
    column_display_pk = True
    column_list = ("id", "mobile", "card_status", "card_money", "card_credit", "name")
    column_choices = dict(
        card_status=[(0, u'正常'), (1, u'冻结')]
    )
    form_choices = dict(
        card_status=[('0', u'正常'), ('1', u'冻结')]
    )
    column_searchable_list = ('mobile', 'name')

    def __init__(self, db, **kwargs):
        ModelView.__init__(self, User, db, **kwargs)

    def is_accessible(self):
        return login.current_user.is_normal_manageruser()

    def scaffold_form(self):
        """改写form"""
        form_class = super(UserView, self).scaffold_form()
        delete_attrs(form_class, ('sign_up_date', 'pub', 'open_id', 'card_date'))
        return form_class

    def get_list(self, page, sort_column, sort_desc, search, filters, execute=True, pub_id=None):
        """
        得到过滤的视图
        """

        # Will contain names of joined tables to avoid duplicate joins
        joins = set()

        query = self.get_query()
        count_query = self.get_count_query()

        if pub_id is None:
            flash(u"系统错误，没有查询到pub_id", 'error')
            raise ValueError
        else:
            query = query.filter(User.pub_id == pub_id)

        # Apply search criteria
        if self._search_supported and search:
            # Apply search-related joins
            if self._search_joins:
                for jn in self._search_joins.values():
                    query = query.join(jn)
                    count_query = count_query.join(jn)

                joins = set(self._search_joins.keys())

            # Apply terms
            terms = search.split(' ')

            for term in terms:
                if not term:
                    continue

                stmt = tools.parse_like_term(term)
                filter_stmt = [c.ilike(stmt) for c in self._search_fields]
                query = query.filter(or_(*filter_stmt))
                count_query = count_query.filter(or_(*filter_stmt))

        # Apply filters
        if filters and self._filters:
            for idx, value in filters:
                flt = self._filters[idx]

                # Figure out joins
                tbl = flt.column.table.name

                join_tables = self._filter_joins.get(tbl, [])

                for table in join_tables:
                    if table.name not in joins:
                        query = query.join(table)
                        count_query = count_query.join(table)
                        joins.add(table.name)

                # Apply filter
                query = flt.apply(query, value)
                count_query = flt.apply(count_query, value)

        # Calculate number of rows
        count = count_query.scalar()

        # Auto join
        for j in self._auto_joins:
            query = query.options(joinedload(j))

        # Sorting
        if sort_column is not None:
            if sort_column in self._sortable_columns:
                sort_field = self._sortable_columns[sort_column]

                query, joins = self._order_by(query, joins, sort_field, sort_desc)
        else:
            order = self._get_default_order()

            if order:
                query, joins = self._order_by(query, joins, order[0], order[1])

        # Pagination
        if page is not None:
            query = query.offset(page * self.page_size)

        query = query.limit(self.page_size)

        # Execute if needed
        if execute:
            query = query.all()

        return count, query

    @expose('/')
    def index_view(self):
        """
            List view
        """
        # Grab parameters from URL
        page, sort_idx, sort_desc, search, filters = self._get_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(sort_idx)
        if sort_column is not None:
            sort_column = sort_column[0]

        pub_id = self.get_pub_id()

        # Get count and data
        count, data = self.get_list(page, sort_column, sort_desc,
                                    search, filters, pub_id=pub_id)

        # Calculate number of pages
        num_pages = count // self.page_size
        if count % self.page_size != 0:
            num_pages += 1

        # Pregenerate filters
        if self._filters:
            filters_data = dict()

            for idx, f in enumerate(self._filters):
                flt_data = f.get_options(self)

                if flt_data:
                    filters_data[idx] = flt_data
        else:
            filters_data = None

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_url('.index_view', p, sort_idx, sort_desc,
                                 search, filters)

        def sort_url(column, invert=False):
            desc = None

            if invert and not sort_desc:
                desc = 1

            return self._get_url('.index_view', page, column, desc,
                                 search, filters)

        # Actions
        actions, actions_confirmation = self.get_actions_list()

        return self.render(self.list_template,
                               data=data,
                               # List
                               list_columns=self._list_columns,
                               sortable_columns=self._sortable_columns,
                               # Stuff
                               enumerate=enumerate,
                               get_pk_value=self.get_pk_value,
                               get_value=self.get_list_value,
                               return_url=self._get_url('.index_view',
                                                        page,
                                                        sort_idx,
                                                        sort_desc,
                                                        search,
                                                        filters),
                               # Pagination
                               count=count,
                               pager_url=pager_url,
                               num_pages=num_pages,
                               page=page,
                               # Sorting
                               sort_column=sort_idx,
                               sort_desc=sort_desc,
                               sort_url=sort_url,
                               # Search
                               search_supported=self._search_supported,
                               clear_search_url=self._get_url('.index_view',
                                                              None,
                                                              sort_idx,
                                                              sort_desc),
                               search=search,
                               # Filters
                               filters=self._filters,
                               filter_groups=self._filter_groups,
                               filter_types=self._filter_types,
                               filter_data=filters_data,
                               active_filters=filters,

                               # Actions
                               actions=actions,
                               actions_confirmation=actions_confirmation)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """
            Edit model view
        """
        return_url = request.args.get('url') or url_for('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            return redirect(return_url)

        model.card_status = ((model.card_status or 0) and 1)  # 使用1与0

        form = self.edit_form(obj=model)

        if validate_form_on_submit(form):
            if self.update_model(form, model):
                if '_continue_editing' in request.form:
                    flash(gettext('Model was successfully saved.'))
                    return redirect(request.full_path)
                else:
                    return redirect(return_url)

        return self.render(self.edit_template,
                           model=model,
                           form=form,
                           form_opts=get_form_opts(self),
                           form_rules=self._form_edit_rules,
                           return_url=return_url)

    def get_pub_id(self):
        try:
            pub_id = int(login.current_user.pub_id)
        except:
            pub_id = None

        return pub_id