# coding: utf-8

"""后台添加新酒吧"""
import logging
import os

from flask.ext.admin.contrib.sqla import ModelView
from flask import flash, redirect, request, url_for
from flask.ext.admin.base import expose
from flask.ext.admin.babel import gettext
from flask.ext.admin.model.helpers import get_mdict_item_or_list
from flask.ext.admin.helpers import validate_form_on_submit
from flask.ext.admin.form import get_form_opts
from wtforms.fields import TextField, FileField
from wtforms import validators
from flask.ext import login
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from flask.ext.admin.contrib.sqla import tools

from ..models.pub import Pub
from ..models.admin_user import AdminUser
from ..utils.others import form_to_dict
from ..utils.ex_file import time_file_name, allowed_file_extension
from ..utils.ex_object import delete_attrs
from ..weixin.menu import create_menu
from werkzeug import secure_filename

from ..setting import (PICTURE_ALLOWED_EXTENSION, PUB_PICTURE_BASE_PATH, PUB_PICTURE_REL_PATH)

log = logging.getLogger("flask-admin.sqla")


class PubView(ModelView):
    """后台添加酒吧和管理员视图"""

    page_size = 30
    can_delete = False
    column_display_pk = True
    column_default_sort = ('id', True)
    column_labels = dict(
        id=u'ID',
        name=u'酒吧名称',
        intro=u'酒吧简介',
        token=u'Token',
        address=u'酒吧地址',
        tel=u'联系方式',
        create_time=u'创建时间',
        stop_time=u'运营截止时间',
        status=u'运营状态'
    )
    column_descriptions = dict(
        token=u'四位，使用数字或者字母，比如3456或者34ab，不能有其他的符号，创建酒吧的时候一定要填写。参考用户手册。',
        appid=u'创建酒吧的时候无需填写，第二次更新酒吧的时候必须填写，以后不要有改动。参考用户手册。',
        secret=u'创建酒吧的时候无需填写，第二次更新酒吧的时候必须填写，以后不要有改动。参考用户手册。',
        stop_time=u'有效运营的截止时间。',
        status=u'运营状态'
    )
    column_exclude_list = ('intro', 'access_token', 'access_token_time', 'secret', 'address', 'tel',
                           'create_time', 'base_path', 'rel_path', 'pic_name', 'logo')
    column_choices = dict(
        status=[(0, u'暂停'), (1, u'运营')]
    )
    form_choices = dict(
        status=[('0', u'暂停'), ('1', u'运营')]
    )

    def __init__(self, db, **kwargs):
        super(PubView, self).__init__(Pub, db, **kwargs)

    def scaffold_form(self):
        """改写form"""
        form_class = super(PubView, self).scaffold_form()
        delete_attrs(form_class, ('access_token_time', 'access_token', 'address', 'tel', 'base_path', 'rel_path',
                                  'pic_name', 'logo', 'create_time'))
        form_class.user = TextField(label=u'酒吧管理员', validators=[validators.required(), validators.length(max=16)])
        form_class.password = TextField(label=u'管理员密码', validators=[validators.required()])

        return form_class

    def create_model(self, form):
        """添加酒吧和管理"""

        try:
            form_dict = form_to_dict(form)
            if not self._valid_form(form_dict):
                flash(u'用户名重复了，换一个呗', 'error')
                return False

            pub = self._get_pub(form_dict)
            self.session.add(pub)
            self.session.commit()

            user = self._get_user(form_dict, pub.id)
            self.session.add(user)
            self.session.commit()

        except Exception, ex:
            flash(gettext('Failed to create model. %(error)s', error=str(ex)), 'error')
            logging.exception('Failed to create model')
            self.session.rollback()
            return False

        return True

    def update_model(self, form, model):
        """更新酒吧和酒吧管理员"""
        try:
            form_dict = form_to_dict(form)

            pub = Pub.query.filter(Pub.id == model.id).first()
            self._update_pub(pub, form_dict)
            user = self._get_pub_admin(model.id)
            if user is None:
                user = self._get_user(form_dict, pub.id)
                self.session.add(user)
            else:
                if not self._update_user(user, form_dict):
                    return False

            self._on_model_change(form, model, False)
            self.session.commit()
            self.after_update_model(model.id)  # 创建菜单，更新数据库资料
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to update model. %(error)s', error=str(ex)), 'error')
            log.exception('Failed to update model')
            self.session.rollback()

            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def after_update_model(self, pub_id):
        """创建菜单"""
        create_menu(pub_id)

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

        user = AdminUser.query.filter(AdminUser.pub_id == id).filter(AdminUser.admin == '111').first()
        if user is None:
            flash(u'这个酒吧还没有管理员哦')
            model.user = None
            model.password = None
        else:
            model.user = user.name
            model.password = user.password

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

    def _valid_form(self, form_dict):
        # 验证用户名是否重复
        if not self._has_user(form_dict['user']):
            return True

        return False

    def _has_user(self, user, model=None):
        """检查用户是否存在，不存在返回False"""
        if model is None:
            return bool(AdminUser.query.filter(AdminUser.name == user).count())
        else:
            return False

    def _get_user(self, form_dict, pub_id):
        """通过字典返回一个user类"""
        return AdminUser(name=form_dict['user'], password=form_dict['password'], admin='111', pub_id=pub_id)

    def _get_pub(self, form_dict):
        """通过字典返回一个pub类"""
        return Pub(name=form_dict['name'],
                   intro=form_dict.get('intro', None),
                   token=form_dict.get('token'),
                   status=form_dict.get('status'),
                   stop_time=form_dict.get('stop_time', None))

    def _get_pub_admin(self, pub_id, admin='111'):
        """通过酒吧id获得酒吧管理员"""
        return AdminUser.query.filter(AdminUser.pub_id == pub_id).filter(AdminUser.admin == '111').first()

    def _update_pub(self, pub, form_dict):
        pub.update(name=form_dict.get('name'),
                   intro=form_dict.get('intro', None),
                   appid=form_dict.get('appid'),
                   secret=form_dict.get('secret'),
                   stop_time=form_dict.get('stop_time', None),
                   status=form_dict.get('status'))

    def _update_user(self, user, form_dict):
        """检查名字是否重复，然后添加"""
        user_count = AdminUser.query.filter(AdminUser.name == form_dict.get('user')).count()
        if (user.name == form_dict.get('user')) or (user_count == 0):
            user.update(name=form_dict.get('user'),
                        password=form_dict.get('password'))
            return True

        flash(u'用户名重复了', 'error')
        return False

    def is_accessible(self):
        return login.current_user.is_normal_superuser()


class SinglePubView(PubView):
    """酒吧管理员管理管理自己酒吧的视图"""

    can_create = False
    can_delete = False
    column_display_pk = True

    column_exclude_list = ('intro', 'access_token', 'access_token_time', 'secret', 'address', 'tel',
                           'create_time', 'base_path', 'rel_path', 'pic_name', 'logo', 'token', 'appid')

    def __init__(self, db, **kwargs):
        ModelView.__init__(self, Pub, db, **kwargs)

    def scaffold_form(self):
        """改写form"""
        form_class = super(PubView, self).scaffold_form()
        delete_attrs(form_class, ('access_token_time', 'access_token', 'token', 'appid', 'secret', 'create_time',
                                  'stop_time', 'status', 'base_path', 'rel_path', 'pic_name', 'logo'))
        form_class.user = TextField(label=u'酒吧管理员', validators=[validators.required(), validators.length(max=16)])
        form_class.password = TextField(label=u'管理员密码', validators=[validators.required()])
        form_class.picture = FileField(label=u'酒吧图片',
                                       description=u'为了更好的展示效果，严格使用640 * 288的图片，仅支持png与jpeg(jpg)格式')

        return form_class

    def is_accessible(self):
        return login.current_user.is_normal_manageruser()

    def update_model(self, form, model):
        """更新酒吧和酒吧管理员"""
        try:
            form_dict = form_to_dict(form)

            pub = Pub.query.filter(Pub.id == model.id).first()
            self._update_pub(pub, form_dict)
            user = self._get_pub_admin(model.id)
            if user is None:
                user = self._get_user(form_dict, pub.id)
                self.session.add(user)
            else:
                if not self._update_user(user, form_dict):
                    return False

            self._on_model_change(form, model, False)
            self.session.commit()
            flash(u'用户资料与酒吧资料保存成功', 'info')

            pub_pictures = request.files.getlist("picture")
            if not save_pub_pictures(pub_pictures, model, update=1):
                return False  # 保存图片， 同时更新model的路径消息

            self.session.commit()  # 保存图片资料

            self.after_update_model(model.id)  # 创建菜单，更新数据库资料
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to update model. %(error)s', error=str(ex)), 'error')
            log.exception('Failed to update model')
            self.session.rollback()

            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def _update_pub(self, pub, form_dict):
        pub.update(name=form_dict.get('name'),
                   intro=form_dict.get('intro', None),
                   address=form_dict.get('address'),
                   tel=form_dict.get('tel'))

    def get_list(self, page, sort_column, sort_desc, search, filters, execute=True, pub_id=None):
        """
            Return models from the database.

            :param page:
                Page number
            :param sort_column:
                Sort column name
            :param sort_desc:
                Descending or ascending sort
            :param search:
                Search query
            :param execute:
                Execute query immediately? Default is `True`
            :param filters:
                List of filter tuples
        """

        # Will contain names of joined tables to avoid duplicate joins
        joins = set()

        query = self.get_query()
        count_query = self.get_count_query()

        if pub_id is None:
            flash(u"系统错误，没有查询到pub_id", 'error')
            raise ValueError
        else:
            query = query.filter(Pub.id == pub_id)

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

    # Views
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

    def get_pub_id(self):
        try:
            pub_id = int(login.current_user.pub_id)
        except:
            pub_id = None

        return pub_id


def save_pub_pictures(pictures, model, update=None):
    """保存酒吧图片，同时删除原来的图片"""

    for picture in pictures:
        if (update is not None) and (model is not None):
            old_picture = str(model.base_path) + str(model.rel_path) + '/' + str(model.pic_name)
        if picture.filename == '':  # 或许没有图片
            return True
        if not allowed_file_extension(picture.filename, PICTURE_ALLOWED_EXTENSION):
            flash(u'图片格式不支持啊，png，jpeg支持', 'error')
            return False
        upload_name = picture.filename
        base_path = PUB_PICTURE_BASE_PATH
        rel_path = PUB_PICTURE_REL_PATH
        pic_name = time_file_name(secure_filename(upload_name))
        picture.save(os.path.join(base_path+rel_path+'/', pic_name))

        model.base_path = base_path
        model.rel_path = rel_path
        model.pic_name = pic_name

        if (update is not None) and (model is not None):
            try:
                os.remove(old_picture)
            except:
                flash("remove %s failed!", old_picture)

        return True