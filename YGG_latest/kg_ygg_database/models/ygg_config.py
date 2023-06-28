import psycopg2
from mysql import connector
import odoo


from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)
import psycopg2.extensions


class PsycoConnection(psycopg2.extensions.connection):
    def lobject(*args, **kwargs):
        pass


# import pyodbc
# import pandas as pd


class YggConfig(models.Model):
    _name = 'ygg.config'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'YGG DB Configuration'

    name = fields.Char("Name", required=True)
    url = fields.Char("Server Address", required=True)
    port_no = fields.Integer("Port No")
    db_name = fields.Char("Database Name", required=True)
    login = fields.Char("Username", required=True)
    password = fields.Char("Password", required=True)
    db_type = fields.Selection([('mssql', 'MSSQL'), ('mysql', 'MySql'), ('psql', 'Postgres')], required=True, default='mssql')
    product_id = fields.Many2one('product.product')
    ygg_config_lines = fields.One2many('ygg.config.line', 'ygg_config_id')

    def run_manually(self):
        server_url = self.url
        port_no = self.port_no
        username = self.login
        db_name = self.db_name
        password = self.password
        if self.db_type == 'mssql':
            conn = pymssql.connect(server=server_url, user=username, password=password, database=db_name, as_dict=True)
            cursor = conn.cursor()
            for line in self.ygg_config_lines:
                # if line.upt_today:
                freq_days = line.update_interval_id.interval
                freq = line.update_interval_id.frequency
                line.last_upt_date = fields.Datetime.today()
                if freq == 'days':
                    line.next_upt_date = fields.Datetime.today() + timedelta(days=freq_days)
                elif freq == 'hours':
                    line.next_upt_date = fields.Datetime.today() + timedelta(hours=freq_days)
                elif freq == 'weeks':
                    line.next_upt_date = fields.Datetime.today() + timedelta(weeks=freq_days)
                elif freq == 'months':
                    line.next_upt_date = fields.Datetime.today() + relativedelta(months=freq_days)
                else:
                    line.next_upt_date = fields.Datetime.today() + relativedelta(years=freq_days)
                if line.next_upt_date <= fields.Datetime.today() and not line.upt_today:
                    line.upt_today = True
                    primary_key = line.ygg_table_id.field_lines.filtered(lambda x: x.primary_key == 'yes')
                    odoo_fields = ','.join(line.ygg_table_id.field_lines.mapped('odoo_field_id.name'))
                    ygg_fields = ','.join(line.ygg_table_id.field_lines.mapped('ygg_field_name'))
                    my_query = "SELECT "+ygg_fields+" FROM "+line.ygg_table_id.name+""
                    cursor.execute(my_query)
                    vals = []
                    for row in cursor.fetchall():
                        vals.append(row)
                    for val in vals:
                        f = {'first': False}
                        f.update(val)
                        val = f
                        query = """SELECT id,%s FROM %s WHERE %s='%s'""" % (odoo_fields, line.ygg_table_id.odoo_model_id.model.replace('.', '_'), primary_key.odoo_field_id.name, val[primary_key.odoo_field_id.name])
                        self._cr.execute(query)
                        result = self._cr.dictfetchall()
                        if result:
                            val['first'] = result[0]['id']
                            keys = list(result[0].keys())
                            vals = list(val.values())
                            res = {}
                            for k in range(len(keys)):
                                res[keys[k]] = vals[k]
                            obj = self.env[line.ygg_table_id.odoo_model_id.model].browse(result[0]['id'])
                            obj.write(res)
                        else:
                            keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
                            del val['first']
                            vals = list(val.values())
                            res = {}
                            for k in range(len(keys)):
                                res[keys[k]] = vals[k]
                            self.env[line.ygg_table_id.odoo_model_id.model].create(res)
                else:
                    line.upt_today = False
            conn.close()
        elif self.db_type == 'mysql':
            mydb = connector.connect(
                host=server_url,
                user=username,
                password=password,
                database=db_name)
            cursor = mydb.cursor()
            print("hhhhhhhhh")
            # my_query = "SELECT * FROM ygag_corporate_corporategift order by id desc limit 10 "
            # my_query = "SELECT * FROM ygag_corporate_corporategift order by id desc limit 10 "
            # my_query = "SELECT * FROM ygag_corporate_corporatepurchaserequest"
            # cursor.execute(my_query)

            columns = [column[0] for column in cursor.description]
            vals = []
            for row in cursor.fetchall():
                vals.append(dict(zip(columns, row)))

            print("vals", vals)

            # my_query = "SHOW TABLES;"
            # cursor.execute(my_query)
            #
            # columns = [column[0] for column in cursor.description]
            # vals = []
            # for row in cursor.fetchall():
            #     vals.append(dict(zip(columns, row)))
            #
            # print("TABLES", vals)

            for line in self.ygg_config_lines:
                # if line.upt_today:
                freq_days = line.update_interval_id.interval
                freq = line.update_interval_id.frequency
                line.last_upt_date = fields.Datetime.today()
                if freq == 'days':
                    line.next_upt_date = fields.Datetime.today() + timedelta(days=freq_days)
                elif freq == 'hours':
                    line.next_upt_date = fields.Datetime.today() + timedelta(hours=freq_days)
                elif freq == 'weeks':
                    line.next_upt_date = fields.Datetime.today() + timedelta(weeks=freq_days)
                elif freq == 'months':
                    line.next_upt_date = fields.Datetime.today() + relativedelta(months=freq_days)
                else:
                    line.next_upt_date = fields.Datetime.today() + relativedelta(years=freq_days)
                if line.next_upt_date <= fields.Datetime.today() and not line.upt_today:
                    line.upt_today = True
                    primary_key = line.ygg_table_id.field_lines.filtered(lambda x: x.primary_key == 'yes')
                    many2one_line = line.ygg_table_id.field_lines.filtered(lambda x: x.ygg_field_type == 'many2one')
                    ygg_fields = ','.join(line.ygg_table_id.field_lines.mapped('ygg_field_name'))
                    my_query = "SELECT "+ygg_fields+" FROM "+line.ygg_table_id.name+" order by id desc limit 200 "
                    # my_query = "SELECT "+ygg_fields+" FROM "+line.ygg_table_id.name
                    print("my_query", my_query)
                    cursor.execute(my_query)
                    columns = [column[0] for column in cursor.description]
                    vals = []
                    for row in cursor.fetchall():
                        vals.append(dict(zip(columns, row)))

                    for val in vals:
                        print("val", val)
                        keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
                        values = list(val.values())
                        res = {'db_name': db_name}
                        # res = {}
                        for k in range(len(keys)):
                            res[keys[k]] = values[k]
                        # if line.ygg_field_type == 'many2one':
                        #     rel_obj = self.env[line.odoo_related_model_id].browse(int(val[line.ygg_field_name]))
                        #     res[line.ygg_field_name] = rel_obj.id
                        if line.ygg_table_id.odoo_model_id.model == 'product.product':
                            res['is_brand'] = True
                            res['detailed_type'] = 'product'
                        if line.ygg_table_id.odoo_model_id.model == 'ygg.orders.order':
                            res['product_id'] = self.product_id.id

                        if line.ygg_table_id.odoo_model_id.model == 'res.partner':
                            res['customer_rank'] = 1

                        if primary_key.ygg_field_type == 'integer':
                            obj = self.env[line.ygg_table_id.odoo_model_id.model].search(
                                [(primary_key.odoo_field_id.name, '=', int(val[primary_key.ygg_field_name]))])
                        elif primary_key.ygg_field_type == 'char':
                            obj = self.env[line.ygg_table_id.odoo_model_id.model].search(
                                [(primary_key.odoo_field_id.name, '=', str(val[primary_key.ygg_field_name]))])
                        else:
                            obj = self.env[line.ygg_table_id.odoo_model_id.model].search(
                                [(primary_key.odoo_field_id.name, '=', val[primary_key.ygg_field_name])])
                        for m2o_line in many2one_line:
                            if res[m2o_line.odoo_field_id.name]:
                                res[m2o_line.odoo_field_id.name] = self.env[m2o_line.odoo_related_model_id].search([('ygg_record_id', '=', int(res[m2o_line.odoo_field_id.name]))]).id
                                # print("+++++++++++", res[m2o_line.odoo_field_id.name])
                        print("res", res)
                        if obj:
                            obj.write(res)
                        else:
                            if res.get(primary_key.odoo_field_id.name):
                                self.env[line.ygg_table_id.odoo_model_id.model].create(res)

                        # f = {'first': False}
                        # f.update(val)
                        # val = f
                        # query = """SELECT id,%s FROM %s WHERE %s='%s'""" % (odoo_fields, line.ygg_table_id.odoo_model_id.model.replace('.', '_'), primary_key.odoo_field_id.name, val[primary_key.odoo_field_id.name])
                        # self._cr.execute(query)
                        # result = self._cr.dictfetchall()
                        # if result:
                        #     val['first'] = result[0]['id']
                        #     keys = list(result[0].keys())
                        #     vals = list(val.values())
                        #     res = {}
                        #     for k in range(len(keys)):
                        #         res[keys[k]] = vals[k]
                        #     obj = self.env[line.ygg_table_id.odoo_model_id.model].browse(result[0]['id'])
                        #     obj.write(res)
                        # else:
                        #     keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
                        #     del val['first']
                        #     vals = list(val.values())
                        #     res = {}
                        #     for k in range(len(keys)):
                        #         res[keys[k]] = vals[k]
                        #     self.env[line.ygg_table_id.odoo_model_id.model].create(res)

                else:
                    line.upt_today = False

            # conn.close()
        else:
            # connection_info = {'database': 'YGG', 'application_name': 'odoo-50151', 'port': 5432, 'user': 'odoo16',
            #                    'sslmode': 'prefer'}
            # result = psycopg2.connect(
            #     connection_factory=PsycoConnection,
            #     **connection_info)
            print("ssss")
            con = None
            cursor = None
            try:
                con = psycopg2.connect(
                    host=server_url,
                    user=username,
                    password=password,
                    database=db_name,
                    port=port_no
                )

                cursor = con.cursor()
                cur = con.cursor()
                # cursor.execute('SELECT * FROM brand_brand')
                # # data = cursor.fetchall()
                # columns = [column[0] for column in cursor.description]
                # vals = []
                # for row in cursor.fetchall():
                #     vals.append(dict(zip(columns, row)))
                #
                # print("TABLES", vals)

                for line in self.ygg_config_lines:
                    # if line.upt_today:
                    freq_days = line.update_interval_id.interval
                    freq = line.update_interval_id.frequency
                    line.last_upt_date = fields.Datetime.today()
                    if freq == 'days':
                        line.next_upt_date = fields.Datetime.today() + timedelta(days=freq_days)
                    elif freq == 'hours':
                        line.next_upt_date = fields.Datetime.today() + timedelta(hours=freq_days)
                    elif freq == 'weeks':
                        line.next_upt_date = fields.Datetime.today() + timedelta(weeks=freq_days)
                    elif freq == 'months':
                        line.next_upt_date = fields.Datetime.today() + relativedelta(months=freq_days)
                    else:
                        line.next_upt_date = fields.Datetime.today() + relativedelta(years=freq_days)
                    if line.next_upt_date <= fields.Datetime.today() and not line.upt_today:
                        line.upt_today = True
                        primary_key = line.ygg_table_id.field_lines.filtered(lambda x: x.primary_key == 'yes')
                        many2one_line = line.ygg_table_id.field_lines.filtered(lambda x: x.ygg_field_type == 'many2one')
                        datetime_lines = line.ygg_table_id.field_lines.filtered(lambda x: x.ygg_field_type == 'datetime')
                        ygg_fields = ','.join(line.ygg_table_id.field_lines.mapped('ygg_field_name'))
                        # my_query = "SELECT " + ygg_fields + " FROM " + line.ygg_table_id.name+" order by id desc limit 10"
                        if line.ygg_table_id.name == 'brand_brand':
                            my_query = "SELECT " + ygg_fields + ",company_id FROM " + line.ygg_table_id.name
                            keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
                            keys.append('company_id')
                        else:
                            my_query = "SELECT " + ygg_fields + " FROM " + line.ygg_table_id.name
                            keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
                        cursor.execute(my_query)
                        columns = [column[0] for column in cursor.description]
                        vals = []
                        for row in cursor.fetchall():
                            vals.append(dict(zip(columns, row)))

                        for val in vals:

                            values = list(val.values())
                            res = {'db_name': db_name}
                            # if line.ygg_table_id.odoo_model_id.model == 'ygg.orders.order':
                            #     if val['cart_id']:


                            #     res['product_id'] = self.product_id.id
                            if line.ygg_table_id.odoo_model_id.model == 'res.partner' and db_name == 'ygag_merchant_console_db_1':
                                res['supplier_rank'] = True
                            for k in range(len(keys)):
                                res[keys[k]] = values[k]
                            print("RES", res)
                            if primary_key.ygg_field_type == 'integer':
                                obj = self.env[line.ygg_table_id.odoo_model_id.model].search(
                                    [(primary_key.odoo_field_id.name, '=', int(val[primary_key.ygg_field_name]))])

                            else:
                                obj = self.env[line.ygg_table_id.odoo_model_id.model].search(
                                    [(primary_key.odoo_field_id.name, '=', val[primary_key.ygg_field_name])])

                            for m2o_line in many2one_line:
                                if res[m2o_line.odoo_field_id.name]:
                                    if m2o_line.odoo_related_model_id == 'res.currency':
                                        res[m2o_line.odoo_field_id.name] = self.env[
                                            'ygg.currency'].search(
                                            [('ygg_record_id', '=',
                                              int(res[m2o_line.odoo_field_id.name]))]).currency_id.id
                                    elif m2o_line.odoo_related_model_id == 'res.country':
                                        res[m2o_line.odoo_field_id.name] = self.env[
                                            'ygg.country'].search(
                                            [('ygg_record_id', '=',
                                              int(res[m2o_line.odoo_field_id.name]))]).country_id.id
                                    elif m2o_line.odoo_field_id.relation == 'res.partner' and db_name == 'ygag_rewards_db':
                                        cur.execute(
                                            'SELECT code,name,account_type FROM corporates_corporate WHERE id = '+str(res[m2o_line.odoo_field_id.name]))

                                        # data = cursor.fetchall()
                                        columns = [column[0] for column in cur.description]
                                        vs = []
                                        for row in cur.fetchall():
                                            vs.append(dict(zip(columns, row)))
                                        print("vvvv", vs)
                                        if vs:
                                            partner = self.env['res.partner'].search(
                                                [('ygg_record_id', '=', vs[0]['code'])]).id
                                            if partner:
                                                res[m2o_line.odoo_field_id.name] = partner
                                            else:
                                                if vs[0].get('customer_type') == 'Pre Paid':
                                                    vs[0]['customer_type'] = 'pre_paid'
                                                res[m2o_line.odoo_field_id.name] = self.env['res.partner'].create({'name': vs[0]['name'],
                                                                                'ygg_record_id': vs[0]['code'],
                                                                                'db_name': db_name,
                                                                                'customer_type': vs[0]['customer_type']
                                                                                                                   }).id

                                    elif m2o_line.odoo_field_id.relation == 'product.product' and db_name == 'ygag_rewards_db':
                                        print("keriiiii")
                                        cur.execute(
                                            'SELECT code,name FROM stores_brand WHERE id = ' + str(
                                                res[m2o_line.odoo_field_id.name]))

                                        # data = cursor.fetchall()
                                        columns = [column[0] for column in cur.description]
                                        vs = []
                                        for row in cur.fetchall():
                                            vs.append(dict(zip(columns, row)))
                                            print("vss",vs)
                                        if vs:
                                            product = self.env['product.product'].search(
                                                [('product_code', '=', vs[0]['code'])], limit=1).id
                                            if product:
                                                res[m2o_line.odoo_field_id.name] = product
                                            else:
                                                res[m2o_line.odoo_field_id.name] = self.env['product.product'].create(
                                                    {'name': vs[0]['name'],
                                                     'is_brand': True,
                                                     'detailed_type': 'product',
                                                     'product_code': vs[0]['code'],
                                                     'db_name': db_name,}).id

                                            res[m2o_line.odoo_field_id.name] = False
                                    elif m2o_line.odoo_field_id.relation == 'product.product' and db_name == 'ygag_merchant_console_db_1':
                                        cur.execute(
                                            'SELECT id,code,name FROM brand_brand WHERE id = ' + str(
                                                res[m2o_line.odoo_field_id.name]))

                                        # data = cursor.fetchall()
                                        columns = [column[0] for column in cur.description]
                                        vs = []
                                        for row in cur.fetchall():
                                            vs.append(dict(zip(columns, row)))
                                        if vs:
                                            product = self.env['product.product'].search(
                                                [('product_code', '=', vs[0]['code'])], limit=1).id

                                            if product:
                                                res[m2o_line.odoo_field_id.name] = product
                                            else:
                                                product_obj = self.env['product.product'].create(
                                                    {'name': vs[0]['name'],
                                                     'is_brand': True,
                                                     'detailed_type': 'product',
                                                     'ygg_record_id': vs[0]['id'],
                                                     'product_code': vs[0]['code'],
                                                     'db_name': db_name,}).id
                                                res[m2o_line.odoo_field_id.name] = product_obj
                                                # cur.execute(
                                                #     'SELECT code,name FROM company_company WHERE id = ' + str(
                                                #         res[m2o_line.odoo_field_id.name]))
                                                #
                                                # # data = cursor.fetchall()
                                                # columns = [column[0] for column in cur.description]
                                                # vs = []
                                                # for row in cur.fetchall():
                                                #     vs.append(dict(zip(columns, row)))
                                                #     print("vss", vs)
                                        else:
                                            res[m2o_line.odoo_field_id.name] = False
                                    else:
                                        product_obj = self.env[m2o_line.odoo_related_model_id].search(
                                            [('ygg_record_id', '=', int(res[m2o_line.odoo_field_id.name]))]).id
                                        res[m2o_line.odoo_field_id.name] = product_obj

                            for datetime_line in datetime_lines:
                                if res[datetime_line.odoo_field_id.name]:
                                    mytime = res[datetime_line.odoo_field_id.name]
                                    # if bool(datetime.strptime(str(mytime)[:19], "%Y-%m-%d %H:%M:%S")):
                                    #     mytime = datetime.strptime(str(mytime)[:19], "%Y-%m-%d %H:%M:%S")

                                    myFormat = "%Y-%m-%d %H:%M:%S"

                                    datetime_object = mytime.strftime(myFormat)
                                    res[datetime_line.odoo_field_id.name] = datetime_object

                            print("$$$$$$", res)
                            if res.get('customer_type') == 'Pre Paid':
                                res['customer_type'] = 'pre_paid'
                            if res.get('commission_type') == 'denomination':
                                cur.execute(
                                    'SELECT amount, commission_percentage FROM brand_branddenominationcommission WHERE brand_commission_id = ' + str(
                                        res['ygg_record_id']))

                                # data = cursor.fetchall()
                                columns = [column[0] for column in cur.description]
                                bd = []
                                for row in cur.fetchall():
                                    bd.append(dict(zip(columns, row)))
                                print("bd", bd)
                                res['commission_amount'] = bd[-1]['amount']
                                res['commission_percentage'] = bd[-1]['commission_percentage']
                            if obj:
                                if line.ygg_table_id.odoo_model_id.model == 'product.product' and db_name == 'ygag_merchant_console_db_1':
                                    vendor_id = self.env['res.partner'].sudo().search(
                                        [('db_name', '=', 'ygag_merchant_console_db_1'),
                                         ('ygg_record_id', '=', res['company_id'])])
                                    del res['company_id']
                                    print("========", res)

                                    obj.write(res)

                                    if vendor_id:
                                        commission_line = self.env['product.supplierinfo'].sudo().create(
                                            {'partner_id': vendor_id.id,
                                             'commission_per': vendor_id.commission_percentage,
                                             'product_id':obj.id,
                                             'product_tmpl_id':obj.product_tmpl_id.id,
                                             })
                                        print("commission_line", commission_line)
                                else:
                                    obj.write(res)
                                if line.ygg_table_id.odoo_model_id.model == 'ygg.topup':
                                    if obj.status == 'paid':
                                        if not obj.payment_id:
                                            journal = self.env['account.journal'].browse(int(
                                                self.env['ir.config_parameter'].sudo().get_param('topup_journal_id')))
                                            payment_vals = {
                                                'date': fields.Date.today(),
                                                'amount': obj.amount,
                                                'vz_bank_charge': obj.service_fee,
                                                'payment_type': 'inbound',
                                                'partner_type': 'customer',
                                                'journal_id': journal.id,
                                                'is_topup': True,
                                                'enable_charge': True,
                                                'partner_id': obj.corporate_id.id,
                                                'payment_method_id': self.env.ref(
                                                    'account.account_payment_method_manual_in').id,
                                            }
                                            payment_id = self.env['account.payment'].create(payment_vals)
                                            obj.payment_id = payment_id.id
                                            payment_id.action_post()
                                        # if not obj.move_id:
                                        #     journal = self.env['account.journal'].browse(int(self.env['ir.config_parameter'].sudo().get_param('topup_journal_id')))
                                        #     if obj.corporate_id.topup_account_id:
                                        #         topup_account_id = obj.corporate_id.topup_account_id
                                        #     else:
                                        #         topup_account_id = self.env['ir.config_parameter'].sudo().get_param('topup_account_id')
                                        #     print("JOO", journal)
                                        #     move = self.env['account.move'].create({
                                        #         'move_type': 'entry',
                                        #         'ygg_topup_id': obj.id,
                                        #         'journal_id': journal.id,
                                        #         'date': date.today(),
                                        #         'line_ids': [
                                        #             (0, 0, {
                                        #                 'account_id': journal.default_account_id.id,
                                        #                 'currency_id': obj.currency_id.id,
                                        #                 'debit': obj.amount,
                                        #                 'credit': 0.0,
                                        #             }),
                                        #             (0, 0, {
                                        #                 'account_id': topup_account_id.id,
                                        #                 'currency_id': obj.currency_id.id,
                                        #                 'debit': 0.0,
                                        #                 'credit': obj.amount,
                                        #             }),
                                        #         ],
                                        #     })
                                        #     move.action_post()
                                        #     obj.move_id = move.id
                            else:
                                if line.ygg_table_id.odoo_model_id.model == 'product.product' and db_name == 'ygag_merchant_console_db_1':
                                    vendor_id = self.env['res.partner'].sudo().search(
                                        [('db_name', '=', 'ygag_merchant_console_db_1'),
                                         ('ygg_record_id', '=', res['company_id'])])
                                    del res['company_id']
                                    obj = self.env[line.ygg_table_id.odoo_model_id.model].create(res)

                                    if vendor_id:
                                        commission_line = self.env['product.supplierinfo'].sudo().create(
                                            {'partner_id': vendor_id.id,
                                             'commission_per': vendor_id.commission_percentage,
                                             'product_id':obj.id,
                                             'product_tmpl_id':obj.product_tmpl_id.id, })
                                else:
                                    obj = self.env[line.ygg_table_id.odoo_model_id.model].create(res)

                                if line.ygg_table_id.odoo_model_id.model == 'ygg.topup':
                                    if not obj.payment_id and obj.status == 'paid':
                                        journal = self.env['account.journal'].browse(int(
                                            self.env['ir.config_parameter'].sudo().get_param('topup_journal_id')))
                                        # if not obj.payment_id and obj.status == 'paid':
                                        payment_vals = {
                                            'date': fields.Date.today(),
                                            'amount': obj.amount,
                                            'vz_bank_charge': obj.service_fee,
                                            'payment_type': 'inbound',
                                            'partner_type': 'customer',
                                            'is_topup': True,
                                            'journal_id': journal.id,
                                            'enable_charge': True,
                                            'partner_id': obj.corporate_id.id,
                                            'payment_method_id': self.env.ref(
                                                'account.account_payment_method_manual_in').id,
                                        }
                                        payment_id = self.env['account.payment'].create(payment_vals)
                                        obj.payment_id = payment_id.id
                                        payment_id.action_post()

                                            # journal = self.env['account.journal'].browse(int(self.env['ir.config_parameter'].sudo().get_param('topup_journal_id')))
                                            # if obj.corporate_id.topup_account_id:
                                            #     topup_account_id = obj.corporate_id.topup_account_id
                                            # else:
                                            #     topup_account_id = self.env['ir.config_parameter'].sudo().get_param('topup_account_id')
                                            # move = self.env['account.move'].create({
                                            #     'move_type': 'entry',
                                            #     'ygg_topup_id': obj.id,
                                            #     'journal_id': journal.id,
                                            #     'date': date.today(),
                                            #     'line_ids': [
                                            #         (0, 0, {
                                            #             'account_id': journal.default_account_id.id,
                                            #             'currency_id': obj.currency_id.id,
                                            #             'debit': obj.amount,
                                            #             'credit': 0.0,
                                            #         }),
                                            #         (0, 0, {
                                            #             'account_id': topup_account_id.id,
                                            #             'currency_id': obj.currency_id.id,
                                            #             'debit': 0.0,
                                            #             'credit': obj.amount,
                                            #         }),
                                            #     ],
                                            # })
                                            # move.action_post()
                                            # obj.move_id = move.id

                    else:
                        line.upt_today = False


            except Exception as error:
                print("-->", error)
            finally:
                if cursor is not None:
                    cursor.close()
                if con is not None:
                    con.close()


            # con = psycopg2.connect(
            #     host=server_url,
            #     user=username,
            #     password=password,
            #     database=db_name,
            #     port=port_no,
            # )

            # con = psycopg2.connect(
            #     database="ygag_myrewards_db",
            #     user="odoo",
            #     password="8RKhbDJQKUEiZm3L3-K2Mz_",
            #     host="ygag-myrewards-sandbox-reader.cumby4scrvet.us-east-2.rds.amazonaws.com",
            #     port='5432'
            # )

            # my_query = "SELECT * FROM information_schema.tables;"
            # cursor_obj.execute(my_query)
            # print("----", cursor_obj)

            # if port_no:
            #     url = "http://"+server_url+':'+str(port_no)
            # else:
            #     url = server_url
            #
            # try:
            #     common = xmlrpc.client.ServerProxy(url + '/xmlrpc/2/common')
            #     uid = common.authenticate(db_name, username, password, {})
            # except:
            #     raise UserError(_('Unsupported XML-RPC protocol'))

            # if port_no:
            #     url = server_type + "://" + server_url + ':' + str(port_no)    else:
            #     url = server_type + "://" + server_url
            # try:        common = xmlrpc.client.ServerProxy(url + '/xmlrpc/2/common')
            # uid = common.authenticate(db_name, username, password, {})    except:        raise UserError(
            #     _('Unsupported XML-RPC protocol'))


            # if uid:
            #     models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
            #     # result = models.execute_kw(db_name, uid, password, 'res.partner', 'search', [[['name', '=', '800 PIZZA LLC']]])
            #     for line in self.ygg_config_lines:
            #         freq_days = line.update_interval_id.interval
            #         freq = line.update_interval_id.frequency
            #         print("freq", freq)
            #         line.last_upt_date = fields.Datetime.today()
            #         if freq == 'days':
            #             line.next_upt_date = fields.Datetime.today() + timedelta(days=freq_days)
            #         elif freq == 'hours':
            #             line.next_upt_date = fields.Datetime.today() + timedelta(hours=freq_days)
            #         elif freq == 'weeks':
            #             line.next_upt_date = fields.Datetime.today() + timedelta(weeks=freq_days)
            #         elif freq == 'months':
            #             line.next_upt_date = fields.Datetime.today() + relativedelta(months=freq_days)
            #         else:
            #             line.next_upt_date = fields.Datetime.today() + relativedelta(years=freq_days)
            #         if line.next_upt_date <= line.last_upt_date and not line.upt_today:
            #             line.upt_today = True
            #             primary_key = line.ygg_table_id.field_lines.filtered(lambda x: x.primary_key == 'yes')
            #             odoo_fields = ','.join(line.ygg_table_id.field_lines.mapped('odoo_field_id.name'))
            #             result = models.execute_kw(db_name, uid, password, line.ygg_table_id.ygg_model_id.model, 'search', [[]])
            #             # models.execute_kw(db_name, uid, password, 'res.partner', 'write', [result, {'email': 'test@123.com'}])
            #             # models.execute_kw(db_name, uid, password, 'res.partner', 'create', [{'name': 'TEST MAN', 'email': 'test@123.com'}])
            #             if result:
            #                 values = models.execute_kw(db_name, uid, password, line.ygg_table_id.ygg_model_id.model, 'read', [result], {'fields': line.ygg_table_id.field_lines.mapped('ygg_field_name')})
            #
            #                 for val in values:
            #                     query = """SELECT id,%s FROM %s WHERE %s='%s'""" % (odoo_fields, line.ygg_table_id.odoo_model_id.model.replace('.', '_'), primary_key.odoo_field_id.name, val[primary_key.odoo_field_id.name])
            #                     self._cr.execute(query)
            #                     record = self._cr.dictfetchall()
            #                     if record:
            #                         keys = list(record[0].keys())
            #                         vals = list(val.values())
            #                         res = {}
            #                         for k in range(len(keys)):
            #                             res[keys[k]] = vals[k]
            #                         obj = self.env[line.ygg_table_id.odoo_model_id.model].browse(record[0]['id'])
            #                         obj.write(res)
            #                     else:
            #                         keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
            #                         del val['id']
            #                         vals = list(val.values())
            #                         res = {}
            #                         for k in range(len(keys)):
            #                             res[keys[k]] = vals[k]
            #
            #                         self.env[line.ygg_table_id.odoo_model_id.model].create(res)
            #         else:
            #             line.upt_today = False
            # else:
            #     raise UserError(_('Authentication Failed!!! \nWrong credentials'))

    def _cron_db_configure(self):
        print("_cron_db_configure")
        db_config_obj = self.env['ygg.config'].search([])
        for db in db_config_obj:
            server_url = db.url
            port_no = db.port_no
            username = db.login
            db_name = db.db_name
            password = db.password
            if db.db_type == 'mssql':
                conn = pymssql.connect(server=server_url, user=username, password=password, database=db_name,
                                       as_dict=True)
                print("conn", conn)
                cursor = conn.cursor()
                for line in db.ygg_config_lines:
                    # if line.upt_today:
                    freq_days = line.update_interval_id.interval
                    freq = line.update_interval_id.frequency
                    print("freq--", freq)
                    line.last_upt_date = fields.Datetime.today()
                    if freq == 'days':
                        line.next_upt_date = fields.Datetime.today() + timedelta(days=freq_days)
                    elif freq == 'hours':
                        line.next_upt_date = fields.Datetime.today() + timedelta(hours=freq_days)
                    elif freq == 'weeks':
                        line.next_upt_date = fields.Datetime.today() + timedelta(weeks=freq_days)
                    elif freq == 'months':
                        line.next_upt_date = fields.Datetime.today() + relativedelta(months=freq_days)
                    else:
                        line.next_upt_date = fields.Datetime.today() + relativedelta(years=freq_days)
                    if line.next_upt_date <= fields.Datetime.today() and not line.upt_today:
                        line.upt_today = True
                        primary_key = line.ygg_table_id.field_lines.filtered(lambda x: x.primary_key == 'yes')
                        odoo_fields = ','.join(line.ygg_table_id.field_lines.mapped('odoo_field_id.name'))
                        ygg_fields = ','.join(line.ygg_table_id.field_lines.mapped('ygg_field_name'))
                        my_query = "SELECT " + ygg_fields + " FROM " + line.ygg_table_id.name + ""
                        cursor.execute(my_query)
                        vals = []
                        for row in cursor.fetchall():
                            vals.append(row)
                        for val in vals:
                            f = {'first': False}
                            f.update(val)
                            val = f
                            query = """SELECT id,%s FROM %s WHERE %s='%s'""" % (
                            odoo_fields, line.ygg_table_id.odoo_model_id.model.replace('.', '_'),
                            primary_key.odoo_field_id.name, val[primary_key.odoo_field_id.name])
                            self._cr.execute(query)
                            result = self._cr.dictfetchall()
                            if result:
                                val['first'] = result[0]['id']
                                keys = list(result[0].keys())
                                vals = list(val.values())
                                res = {}
                                for k in range(len(keys)):
                                    res[keys[k]] = vals[k]
                                obj = self.env[line.ygg_table_id.odoo_model_id.model].browse(result[0]['id'])
                                obj.write(res)
                            else:
                                keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
                                del val['first']
                                vals = list(val.values())
                                res = {}
                                for k in range(len(keys)):
                                    res[keys[k]] = vals[k]
                                self.env[line.ygg_table_id.odoo_model_id.model].create(res)
                    else:
                        line.upt_today = False
                conn.close()
            elif db.db_type == 'mysql':
                mydb = connector.connect(
                    host=server_url,
                    user=username,
                    password=password,
                    database=db_name)
                cursor = mydb.cursor()

                print("---->connection", cursor)
                # cursor.execute("SELECT Id, name, is_incentives, website, account_limit, corporate_type, date_added, date_modified, name_slug, category_id,currency, corporate_code, slug, is_channel_incentive, pdf_type, activation_expiry_month contract_file, credit_limit, number_of_activation_code, enable_validation_data_upload, order_validity_month, lead_medium_id,lead_source_id, lead_industry_id, lead_date, company_name, is_active, is_rewards_corporate, region_id, custom_sender_name,show_sender_name, is_gift_shop_corporate, business_level_category_id, business_level_subcategory_id, industry_information_id, other_industry_information FROM ygag_corporate_corporate;")
                # cursor.execute("SELECT * FROM ygag_corporate_businesslevelcorporatesubcategory;")
                # cursor.execute("SHOW TABLES;")
                # columns = [column[0] for column in cursor.description]
                # vals = []
                # for row in cursor.fetchall():
                #     vals.append(dict(zip(columns, row)))
                # print("VV", vals)

                for line in db.ygg_config_lines:
                    # if line.upt_today:
                    freq_days = line.update_interval_id.interval
                    freq = line.update_interval_id.frequency
                    line.last_upt_date = fields.Datetime.today()
                    if freq == 'days':
                        line.next_upt_date = fields.Datetime.today() + timedelta(days=freq_days)
                    elif freq == 'hours':
                        line.next_upt_date = fields.Datetime.today() + timedelta(hours=freq_days)
                    elif freq == 'weeks':
                        line.next_upt_date = fields.Datetime.today() + timedelta(weeks=freq_days)
                    elif freq == 'months':
                        line.next_upt_date = fields.Datetime.today() + relativedelta(months=freq_days)
                    else:
                        line.next_upt_date = fields.Datetime.today() + relativedelta(years=freq_days)
                    if line.next_upt_date <= fields.Datetime.today() and not line.upt_today:
                        line.upt_today = True
                        primary_key = line.ygg_table_id.field_lines.filtered(lambda x: x.primary_key == 'yes')
                        many2one_line = line.ygg_table_id.field_lines.filtered(lambda x: x.ygg_field_type == 'many2one')
                        odoo_fields = ','.join(line.ygg_table_id.field_lines.mapped('odoo_field_id.name'))
                        ygg_fields = ','.join(line.ygg_table_id.field_lines.mapped('ygg_field_name'))
                        my_query = "SELECT " + ygg_fields + " FROM " + line.ygg_table_id.name + ""
                        cursor.execute(my_query)
                        columns = [column[0] for column in cursor.description]
                        vals = []
                        for row in cursor.fetchall():
                            vals.append(dict(zip(columns, row)))

                        for val in vals:
                            keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
                            values = list(val.values())
                            res = {'db_name': db_name}
                            for k in range(len(keys)):
                                res[keys[k]] = values[k]

                            # if line.ygg_field_type == 'many2one':
                            #     rel_obj = self.env[line.odoo_related_model_id].browse(int(val[line.ygg_field_name]))
                            #     res[line.ygg_field_name] = rel_obj.id

                            if primary_key.ygg_field_type == 'integer':

                                obj = self.env[line.ygg_table_id.odoo_model_id.model].search(
                                    [(primary_key.odoo_field_id.name, '=', int(val[primary_key.ygg_field_name])),
                                     ('db_name', '=', db_name)])
                            else:
                                obj = self.env[line.ygg_table_id.odoo_model_id.model].search(
                                    [(primary_key.odoo_field_id.name, '=', val[primary_key.ygg_field_name]),
                                     ('db_name', '=', db_name)])
                            print("######", res)
                            for m2o_line in many2one_line:
                                if res[m2o_line.odoo_field_id.name]:
                                    if m2o_line.odoo_related_model_id == 'res.currency':
                                        res[m2o_line.odoo_field_id.name] = self.env[
                                            'ygg.currency'].search(
                                            [('ygg_record_id', '=',
                                              int(res[m2o_line.odoo_field_id.name]))]).currency_id.id
                                    elif m2o_line.odoo_related_model_id == 'res.country':
                                        res[m2o_line.odoo_field_id.name] = self.env[
                                            'ygg.country'].search(
                                            [('ygg_record_id', '=',
                                              int(res[m2o_line.odoo_field_id.name]))]).country_id.id
                                    elif m2o_line.odoo_related_model_id == 'res.partner' and db_name == 'ygag_rewards_db':
                                        cursor.execute('SELECT code FROM corporates_corporate WHERE id = ' + res[
                                            m2o_line.odoo_field_id.name])
                                        data = cursor.fetchall()
                                        print("@#@#", data)
                                        res[m2o_line.odoo_field_id.name] = self.env[
                                            'ygg.country'].search(
                                            [('ygg_record_id', '=',
                                              int(res[m2o_line.odoo_field_id.name]))]).country_id.id
                                    else:
                                        res[m2o_line.odoo_field_id.name] = self.env[
                                            m2o_line.odoo_related_model_id].search(
                                            [('ygg_record_id', '=', int(res[m2o_line.odoo_field_id.name]))]).id
                            print("====", res)

                            if obj:
                                obj.write(res)
                            else:
                                self.env[line.ygg_table_id.odoo_model_id.model].create(res)

                            # f = {'first': False}
                            # f.update(val)
                            # print("vvvv", f)
                            # val = f
                            # query = """SELECT id,%s FROM %s WHERE %s='%s'""" % (odoo_fields, line.ygg_table_id.odoo_model_id.model.replace('.', '_'), primary_key.odoo_field_id.name, val[primary_key.odoo_field_id.name])
                            # self._cr.execute(query)
                            # result = self._cr.dictfetchall()
                            # if result:
                            #     val['first'] = result[0]['id']
                            #     keys = list(result[0].keys())
                            #     vals = list(val.values())
                            #     res = {}
                            #     for k in range(len(keys)):
                            #         res[keys[k]] = vals[k]
                            #     obj = self.env[line.ygg_table_id.odoo_model_id.model].browse(result[0]['id'])
                            #     obj.write(res)
                            # else:
                            #     keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
                            #     del val['first']
                            #     vals = list(val.values())
                            #     res = {}
                            #     for k in range(len(keys)):
                            #         res[keys[k]] = vals[k]
                            #     self.env[line.ygg_table_id.odoo_model_id.model].create(res)
                    else:
                        line.upt_today = False
                # conn.close()
            else:
                con = None
                cursor = None
                try:
                    con = psycopg2.connect(
                        host=server_url,
                        user=username,
                        password=password,
                        database=db_name,
                        port=port_no
                    )

                    cursor = con.cursor()
                    # cursor.execute('SELECT * FROM public.orders_order')
                    #
                    # data = cursor.fetchall()
                    # print(data)

                    for line in db.ygg_config_lines:
                        # if line.upt_today:
                        freq_days = line.update_interval_id.interval
                        freq = line.update_interval_id.frequency
                        line.last_upt_date = fields.Datetime.today()
                        if freq == 'days':
                            line.next_upt_date = fields.Datetime.today() + timedelta(days=freq_days)
                        elif freq == 'hours':
                            line.next_upt_date = fields.Datetime.today() + timedelta(hours=freq_days)
                        elif freq == 'weeks':
                            line.next_upt_date = fields.Datetime.today() + timedelta(weeks=freq_days)
                        elif freq == 'months':
                            line.next_upt_date = fields.Datetime.today() + relativedelta(months=freq_days)
                        else:
                            line.next_upt_date = fields.Datetime.today() + relativedelta(years=freq_days)
                        if line.next_upt_date <= fields.Datetime.today() and not line.upt_today:
                            line.upt_today = True
                            primary_key = line.ygg_table_id.field_lines.filtered(lambda x: x.primary_key == 'yes')
                            many2one_line = line.ygg_table_id.field_lines.filtered(
                                lambda x: x.ygg_field_type == 'many2one')
                            datetime_lines = line.ygg_table_id.field_lines.filtered(
                                lambda x: x.ygg_field_type == 'datetime')
                            ygg_fields = ','.join(line.ygg_table_id.field_lines.mapped('ygg_field_name'))
                            my_query = "SELECT " + ygg_fields + " FROM " + line.ygg_table_id.name + ""
                            print("my_query", my_query)
                            cursor.execute(my_query)
                            columns = [column[0] for column in cursor.description]
                            vals = []
                            for row in cursor.fetchall():
                                vals.append(dict(zip(columns, row)))
                            print("VALS", vals)

                            for val in vals:
                                keys = line.ygg_table_id.field_lines.mapped('odoo_field_id.name')
                                values = list(val.values())
                                res = {'db_name': db_name}
                                for k in range(len(keys)):
                                    res[keys[k]] = values[k]

                                if primary_key.ygg_field_type == 'integer':

                                    obj = self.env[line.ygg_table_id.odoo_model_id.model].search(
                                        [(primary_key.odoo_field_id.name, '=', int(val[primary_key.ygg_field_name])),
                                         ('db_name', '=', db_name)])
                                else:
                                    obj = self.env[line.ygg_table_id.odoo_model_id.model].search(
                                        [(primary_key.odoo_field_id.name, '=', val[primary_key.ygg_field_name]),
                                         ('db_name', '=', db_name)])

                                print("OBJECT", obj)
                                for m2o_line in many2one_line:
                                    if res[m2o_line.odoo_field_id.name]:
                                        if m2o_line.odoo_related_model_id == 'res.currency':
                                            res[m2o_line.odoo_field_id.name] = self.env[
                                                'ygg.currency'].search(
                                                [('ygg_record_id', '=', int(res[m2o_line.odoo_field_id.name]))]).currency_id.id
                                        else:
                                            res[m2o_line.odoo_field_id.name] = self.env[
                                                m2o_line.odoo_related_model_id].search(
                                                [('ygg_record_id', '=', int(res[m2o_line.odoo_field_id.name]))]).id

                                for datetime_line in datetime_lines:
                                    if res[datetime_line.odoo_field_id.name]:
                                        mytime = res[datetime_line.odoo_field_id.name]
                                        myFormat = "%Y-%m-%d %H:%M:%S"
                                        datetime_object = mytime.strftime(myFormat)
                                        print("datetime_object", datetime_object)
                                        res[datetime_line.odoo_field_id.name] = datetime_object

                                print("$$$$$$", res)
                                if obj:
                                    obj.write(res)
                                else:
                                    self.env[line.ygg_table_id.odoo_model_id.model].create(res)

                        else:
                            line.upt_today = False


                except Exception as error:
                    print("-->", error)
                finally:
                    if cursor is not None:
                        cursor.close()
                    if con is not None:
                        con.close()


class YggConfigLine(models.Model):
    _name = 'ygg.config.line'
    _order = 'update_sequence'
    _description = 'YGG DB Config Line'

    ygg_config_id = fields.Many2one('ygg.config', 'YGG Configuration')
    ygg_table_id = fields.Many2one('ygg.table', 'YGG Table Name',required=True)
    ygg_table_name = fields.Char('YGG Table Name')
    ygg_field_name = fields.Char('YGG Field Name')
    ygg_model_id = fields.Many2one('ir.model', 'YGG DB Model')
    ygg_field_id = fields.Many2one('ir.model.fields', 'YGG DB Value Field', domain="[('model_id', '=', ygg_model_id)]")
    check_field_id = fields.Many2one('ir.model.fields', 'YGG DB Check Field', domain="[('model_id', '=', ygg_model_id)]")
    odoo_field_name = fields.Char('Odoo Field Name')
    odoo_table_name = fields.Char('Odoo Table Name')
    odoo_relation_id = fields.Many2one('ir.model.relation', 'Relation Model')
    odoo_model_id = fields.Many2one('ir.model', 'Updated Model')
    updated_field_id = fields.Many2one('ir.model.fields', 'Updated Field', domain="[('model_id', '=', odoo_model_id)]")
    odoo_check_field_id = fields.Many2one('ir.model.fields', 'Odoo Check Field', domain="[('model_id', '=', odoo_model_id)]")
    update_sequence = fields.Integer('Update Sequence', default=1)
    update_interval_id = fields.Many2one('ygg.intervals', string='Update Interval')
    last_upt_date = fields.Datetime('Last Updated On')
    next_upt_date = fields.Datetime('Next Update')
    upt_today = fields.Boolean('Updated', default=False)

    @api.onchange('ygg_table_id')
    def get_ygg_table_id(self):
        res = {'domain': {'ygg_table_id': [
            ('db_name', '=', self.ygg_config_id.db_name)]}}
        return res

    # @api.depends('last_upt_date', 'next_upt_date')
    # def _compute_upt_today(self):
    #     for rec in self:
    #         if not rec.last_upt_date and not rec.next_upt_date:
    #             rec.upt_today = True
    #         elif rec.last_upt_date != fields.Date.today() and rec.next_upt_date == fields.Date.today():
    #             rec.upt_today = True
    #         else:
    #             rec.upt_today = False

    # def get_values(self):
    #     query = """SELECT table_name FROM information_schema.tables"""
    #     self._cr.execute(query)
    #     result = self._cr.dictfetchall()
    #     values = []
    #     for val in result:
    #         values.append((val['table_name'], val['table_name']))
    #     return values
    #
    #
    # all_table_name = fields.Selection(selection=get_values)
    #
    # def get_col_values(self):
    #     query = """SELECT column_name FROM information_schema.columns"""
    #     self._cr.execute(query)
    #     result = self._cr.dictfetchall()
    #     values = []
    #     for val in result:
    #         if (val['column_name'], val['column_name']) not in values:
    #             values.append((val['column_name'], val['column_name']))
    #     return values
    #
    # all_table_col_name = fields.Selection(selection=get_col_values)


class YggIntervals(models.Model):
    _name = 'ygg.intervals'
    _description = 'YGG Intervals'

    name = fields.Char("Name")
    interval = fields.Integer("Interval")
    frequency = fields.Selection([('hours', 'Hour(s)'),
                                  ('days', 'Day(s)'),
                                  ('weeks', 'Week(s)'),
                                  ('months', 'Month(s)'),
                                  ('years', 'Year(s)')], default='day', required=True)
