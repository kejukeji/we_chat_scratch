# coding: utf-8

import logging
import os

from flask.ext.admin.contrib.sqla import ModelView
from flask import flash, redirect, request, url_for
from flask.ext.admin.base import expose
from flask.ext.admin.babel import gettext
from flask.ext.admin.model.helpers import get_mdict_item_or_list
from flask.ext.admin.helpers import validate_form_on_submit
from flask.ext.admin.form import get_form_opts
from wtforms.fields import FileField
from flask.ext import login
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from flask.ext.admin.contrib.sqla import tools

from ..models.ticket import Ticket, UserTicket
from ..utils.others import form_to_dict
from ..utils.ex_file import time_file_name, allowed_file_extension
from ..utils.ex_object import delete_attrs
from werkzeug import secure_filename
from ..setting import PICTURE_ALLOWED_EXTENSION, TICKET_PICTURE_BASE_PATH, TICKET_PICTURE_REL_PATH

log = logging.getLogger("flask-admin.sqla")


class TicketView(ModelView):
    """优惠券管理视图"""

    page_size = 30
    can_delete = False
    can_edit = True
    can_create = True
    column_default_sort = ('id', True)
    column_labels = {
        'id': u'ID',
        'title': u'标题',
        'intro': u'介绍',
        'start_time': u'开始时间',
        'stop_time': u'截止时间',
        'status': u'状态',
        'number': u'已领取人数',
        'max_number': u'限制领取人数',
        'pub.name': u'酒吧',
        'repeat': u'重复领取'
    }
    column_choices = {
        'status': [(0, u'下线'), (1, u'上线')],
        'repeat': [(0, u'用户消费之后可以继续领取'), (1, u'每个用户限制领取一次')]
    }
    form_choices = {
        'status': [('0', u'下线'), ('1', u'上线')],
        'repeat': [('0', u'用户消费之后可以继续领取'), ('1', u'每个用户限制领取一次')]
    }
    column_descriptions = {
        'number': u'已经获取了这个优惠券的人数',
        'max_number': u'限制领取优惠券的人数，也就是只有那么多的人能够领取到这个优惠券。如果为0，就是没有限制。'
    }
    column_display_pk = True
    column_list = ('id', 'title', 'start_time', 'stop_time', 'number', 'max_number', 'status')

    def __init__(self, db, **kwargs):
        super(TicketView, self).__init__(Ticket, db, **kwargs)

    def scaffold_form(self):
        """改写form"""
        form_class = super(TicketView, self).scaffold_form()
        delete_attrs(form_class, ('base_path', 'rel_path', 'pic_name', 'pub'))
        form_class.picture = FileField(label=u'优惠券图片', description=u'推荐使用640*288')

        return form_class

    def is_accessible(self):
        return login.current_user.is_normal_manageruser()

    def create_model(self, form):
        """改写flask的新建model的函数"""

        try:
            pictures = request.files.getlist("picture")
            model = self.model(pub_id=self.get_pub_id(), **form_to_dict(form))
            if not check_save_ticket_pictures(pictures, model):
                return False
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
        """改写了update函数"""
        try:
            pictures = request.files.getlist("picture")
            model.update(**form_to_dict(form))
            if not check_save_ticket_pictures(pictures, model, update=1):
                return False
            self.session.commit()
        except Exception, ex:
            flash(gettext('Failed to update model. %(error)s', error=str(ex)), 'error')
            logging.exception('Failed to update model')
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, False)

        return True

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
            query = query.filter(Ticket.pub_id == pub_id)

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

        model.status = ((model.status or 0) and 1)  # 使用1与0
        model.repeat = ((model.repeat or 0) and 1)  # 使用1与0

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


class UserTicketView(ModelView):
    pass


def check_save_ticket_pictures(gift_pictures, model=None, update=None):
    """200*200的图片"""

    for picture in gift_pictures:
        if (update is not None) and (model is not None):
            old_picture = str(model.base_path) + str(model.rel_path) + '/' + str(model.pic_name)
        if picture.filename == '':  # 或许没有图片，那么图片不更新
            return True
        if not allowed_file_extension(picture.filename, PICTURE_ALLOWED_EXTENSION):
            flash(u'图片格式不支持啊，png，jpeg支持', 'error')
            return False
        upload_name = picture.filename
        base_path = TICKET_PICTURE_BASE_PATH
        rel_path = TICKET_PICTURE_REL_PATH
        pic_name = time_file_name(secure_filename(upload_name))
        picture.save(os.path.join(base_path+rel_path+'/', pic_name))

        model.base_path = base_path
        model.rel_path = rel_path
        model.pic_name = pic_name

        if (update is not None) and (model is not None):
            try:
                os.remove(old_picture)
            except:
                display = "remove %s failed" % old_picture
                flash(display, 'error')

        return True