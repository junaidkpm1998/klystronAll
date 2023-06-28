import pymssql
from mysql import connector
import psycopg2.extensions



from odoo import api, fields, models, _


class KGsalesFetchWizard(models.TransientModel):
    """Sales Fetch wizard."""

    _name = 'ygg.sales.fetch.wizard'
    _description = 'Sales Fetch Wizard'

    name = fields.Char(string='Sale Order No')
    database = fields.Many2one('ygg.config', string='Database')

    def button_fetch_sale_order(self):
        server_url = self.database.url
        port_no = self.database.port_no
        username = self.database.login
        db_name = self.database.db_name
        password = self.database.password

        if self.database.db_type == 'mssql':
            conn = pymssql.connect(server=server_url, user=username, password=password, database=db_name, as_dict=True)
            cursor = conn.cursor()

        if self.database.db_type == 'mysql':
            mydb = connector.connect(
                host=server_url,
                user=username,
                password=password,
                database=db_name)
            cursor = mydb.cursor()

        if self.database.db_type == 'psql':
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

            except Exception as error:
                print("--------", error)
            finally:
                if cursor is not None:
                    cursor.close()
                if con is not None:
                    con.close()
