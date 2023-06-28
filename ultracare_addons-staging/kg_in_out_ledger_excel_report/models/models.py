# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Midilaj (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import time
from datetime import date
import pytz
import json
import datetime
import io
from odoo import api, fields, models, _
from odoo.tools import date_utils
from odoo.exceptions import UserError
from datetime import datetime

try:
    from odoo.tools.misc import xlsxwriter, DEFAULT_SERVER_DATETIME_FORMAT
except ImportError:
    import xlsxwriter


class StockReport(models.TransientModel):
    _name = "kg.wizard.stock.history"
    _description = "Current Stock History"

    date_start = fields.Date(required=True, default=date.today().strftime('%Y-01-01'))
    date_end = fields.Date(required=True, default=fields.Date.to_string(date.today()))
    location_id = fields.Many2one('stock.location', string='Locations')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company')
    file_name = fields.Char('File Name')
    type = fields.Selection([
        ('boe', 'BOE Based'),
        ('product', 'Product Based')], default='product',
        help="Select to get report based on BOE or product")

    def export_xls(self):
        if not self.date_start:
            raise UserError(_("Please enter start date"))
        if not self.date_end:
            raise UserError(_("Please enter end date"))

        data = {
            'ids': self.ids,
            'model': self._name,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'type': self.type,
            'location_id': self.location_id.complete_name,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'kg.wizard.stock.history',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'In Out Ledger',
                     },
            'report_type': 'stock_xlsx'
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Add formating for cells in excel
        style_specification_data_blue = workbook.add_format()
        style_specification_data_blue.set_fg_color('#9ACEEB')
        style_specification_data_blue.set_font_name('Times New Roman')
        style_specification_data_blue.set_bold()
        style_specification_data_blue.set_text_wrap()
        style_specification_data_blue.set_align('left')
        style_specification_data_blue.set_border()

        style_specification_data_white = workbook.add_format()
        style_specification_data_white.set_fg_color('white')
        style_specification_data_white.set_font_name('Times New Roman')
        style_specification_data_white.set_bold()
        style_specification_data_white.set_text_wrap()
        style_specification_data_white.set_align('left')
        style_specification_data_white.set_border()

        style_maintenance_majenta = workbook.add_format({})
        style_maintenance_majenta.set_fg_color('#F7D6D0')
        style_maintenance_majenta.set_font_name('Times New Roman')
        style_maintenance_majenta.set_bold()
        style_maintenance_majenta.set_text_wrap()
        style_maintenance_majenta.set_align('left')
        style_maintenance_majenta.set_border()

        style_specifications_majenta = workbook.add_format()
        style_specifications_majenta.set_fg_color('#F7D6D0')
        style_specifications_majenta.set_font_name('Times New Roman')
        style_specifications_majenta.set_bold()
        style_specifications_majenta.set_text_wrap()
        style_specifications_majenta.set_align('left')
        style_specifications_majenta.set_border()

        style_specifications_white = workbook.add_format()
        style_specifications_white.set_fg_color('white')
        style_specifications_white.set_font_name('Times New Roman')
        style_specifications_white.set_bold()
        style_specifications_white.set_text_wrap()
        style_specifications_white.set_align('left')
        style_specifications_white.set_border()

        style_specifications_white_center = workbook.add_format()
        style_specifications_white_center.set_fg_color('white')
        style_specifications_white_center.set_font_name('Times New Roman')
        style_specifications_white_center.set_bold()
        style_specifications_white_center.set_text_wrap()
        style_specifications_white_center.set_align('center')
        style_specifications_white_center.set_border()

        style_specifications_yellow = workbook.add_format()
        style_specifications_yellow.set_fg_color('#ffff94')
        style_specifications_yellow.set_font_name('Times New Roman')
        style_specifications_yellow.set_bold()
        style_specifications_yellow.set_text_wrap()
        style_specifications_yellow.set_align('left')
        style_specifications_yellow.set_border()

        style_specifications_green = workbook.add_format()
        style_specifications_green.set_fg_color('#96e281')
        style_specifications_green.set_font_name('Times New Roman')
        style_specifications_green.set_bold()
        style_specifications_green.set_text_wrap()
        style_specifications_green.set_align('left')
        style_specifications_green.set_border()

        date_start = data['date_start']
        date_end = data['date_end']
        type = data['type']
        location_id = data['location_id']

        if type == 'product':
            print(type, "INNNNNNN")
            internal_picking = self.env['stock.picking.type'].search(
                [('code', '=', 'internal'), ('sequence_code', '=', 'INT'), ('company_id', '=', self.env.company.id)])
            print(internal_picking, "INreerrr")
            existing_ids = []
            move_ids = self.env['stock.move'].search(
                [('state', '=', 'done'), ('date', '<=', date_end), ('date', '>=', date_start),
                 ('picking_type_id', '!=', internal_picking.id), ('company_id', '=', self.env.company.id), '|',
                 ('location_id', '=', location_id), ('location_dest_id', '=', location_id)
                 ], order='date asc')
            print(move_ids, "MOveee")
            sheet = workbook.add_worksheet()
            row = 1
            right_row = 3  # For login details
            col = 0
            sheet.merge_range(row + 1, col, row, col + 10, 'IN OUT LEDGER (PRODUCT BASED)',
                              style_specifications_white_center)
            row = row + 2
            sheet.merge_range(row + 1, col, row, col + 4, self.env.user.company_id.name, style_specification_data_white)
            row = row + 2
            sheet.merge_range(row + 1, col, row, col + 4, "PO BOX : " + str(self.env.user.company_id.zip) + ", " + str(
                self.env.user.company_id.state_id.name) + ", " + str(self.env.user.company_id.country_id.name)
                              , style_specification_data_white)
            row = row + 3
            sheet.merge_range(right_row + 1, col + 6, right_row, col + 10,
                              "Period From : " + date_start + " To " + date_end, style_specification_data_white)
            row = row + 2
            right_row = right_row + 2
            sheet.merge_range(right_row + 1, col + 6, right_row, col + 10, "Login ID : " + self.env.user.name,
                              style_specification_data_white)
            right_row = right_row + 2
            sheet.merge_range(right_row + 1, col + 6, right_row, col + 10,
                              "Location : " + location_id,
                              style_specification_data_white)

            for each in move_ids:
                print(each, "EAchh")
                if each.id not in existing_ids:
                    existing_ids.append(each.id)
                    check_product = []

                    product_move_ids = self.env['stock.move'].search(
                        [('state', '=', 'done'),
                         ('product_id', '=', each.product_id.id), ('date', '<=', date_end),
                         ('date', '>=', date_start), ('picking_type_id', '!=', internal_picking.id),
                         ('company_id', '=', self.env.company.id),
                         '|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)],
                        order='date asc')
                    print(product_move_ids, "Product_moveeeee")

                    balance = 0
                    in_qty_balance = 0
                    out_qty_balance = 0

                    for line in product_move_ids:
                        existing_ids.append(line.id)
                        if line.product_id.id not in check_product:
                            sheet.merge_range(row, col, row, col + 10, line.product_id.default_code,
                                              style_specifications_green)
                            check_product.append(line.product_id.id)
                            row = row + 1
                            col = col
                            header_row = row
                            header_col = col
                            sheet.write(header_row, header_col, 'Doc.Date', style_specification_data_blue)
                            sheet.write(header_row, header_col + 1, 'Type', style_specification_data_blue)
                            sheet.write(header_row, header_col + 2, 'Doc.No.', style_specification_data_blue)
                            sheet.write(header_row, header_col + 3, 'Vendor', style_specification_data_blue)
                            sheet.write(header_row, header_col + 4, 'Reference', style_specification_data_blue)
                            sheet.write(header_row, header_col + 5, 'Loc', style_specification_data_blue)
                            sheet.write(header_row, header_col + 6, 'Cost', style_specification_data_blue)
                            sheet.write(header_row, header_col + 7, 'Rate', style_specification_data_blue)
                            sheet.write(header_row, header_col + 8, 'In Qty', style_specification_data_blue)
                            sheet.write(header_row, header_col + 9, 'Out Qty', style_specification_data_blue)
                            sheet.write(header_row, header_col + 10, 'Balance', style_specification_data_blue)
                            sheet.write(header_row, header_col + 11, 'Balance(Amt)', style_specification_data_blue)
                            row = row + 1
                            col = col

                        picking_name = line.picking_id.name
                        if line.picking_id.name == False:
                            picking_name = 'NULL'

                        vendor_name = ' '
                        if line.picking_id.partner_id.name:
                            if line.picking_id.picking_type_code == 'incoming':
                                vendor_name = line.picking_id.partner_id.name
                            if line.picking_id.picking_type_code != 'incoming':
                                vendor_name = ' '

                        in_qty = 0
                        out_qty = 0
                        if (line.location_usage in ('internal', 'transit')) and (
                                line.location_dest_usage not in ('internal', 'transit')):
                            out_qty = -abs(line.product_uom_qty)
                            out_qty_balance -= out_qty
                        if (line.location_usage not in ('internal', 'transit')) and (
                                line.location_dest_usage in ('internal', 'transit')):
                            in_qty = line.product_uom_qty
                            in_qty_balance += in_qty

                        balance = in_qty_balance - out_qty_balance
                        balance_amt = line.product_id.standard_price * balance
                        # opening_balance = in_qty_balance - out_qty_balance
                        if product_move_ids:
                            vendor_name = product_move_ids[0].picking_id.partner_id.name or ''

                        sheet.write(row, col, str(line.date.date()), style_specification_data_white)
                        sheet.write(row, col + 1, type, style_specification_data_white)
                        sheet.write(row, col + 2, picking_name, style_specification_data_white)
                        sheet.write(row, col + 3, vendor_name, style_specification_data_white)
                        sheet.write(row, col + 4, line.reference or ' ', style_specification_data_white)
                        sheet.write(row, col + 5, line.location_id.name, style_specification_data_white)
                        sheet.write(row, col + 6, f"{line.product_tmpl_id.standard_price:.2f}",
                                    style_specification_data_white)
                        sheet.write(row, col + 7,
                                    f"{line.purchase_line_id.price_unit:.2f}" or f"{line.sale_line_id.price_unit:.2f}" or 0,
                                    style_specification_data_white)
                        sheet.write(row, col + 8, f"{in_qty:.2f}", style_specification_data_white)
                        sheet.write(row, col + 9, f"{out_qty:.2f}", style_specification_data_white)
                        sheet.write(row, col + 10, f"{balance:.2f}", style_specification_data_white)
                        sheet.write(row, col + 11, f"{balance_amt:.2f}", style_specification_data_white)
                        # sheet.write(row, col + 12, f"{vendor_name}", style_specification_data_white)
                        row = row + 1
                        col = col
                    sheet.write(row, col + 10, f"{balance:.2f}", style_specifications_yellow)
                    row = row + 1
                    col = col
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    # def get_xlsx_report(self, data, response):
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #
    #     style_specification_data_blue = workbook.add_format()
    #     style_specification_data_blue.set_fg_color('#9ACEEB')
    #     style_specification_data_blue.set_font_name('Times New Roman')
    #     style_specification_data_blue.set_bold()
    #     style_specification_data_blue.set_text_wrap()
    #     style_specification_data_blue.set_align('left')
    #     style_specification_data_blue.set_border()
    #
    #     style_specification_data_white = workbook.add_format()
    #     style_specification_data_white.set_fg_color('white')
    #     style_specification_data_white.set_font_name('Times New Roman')
    #     style_specification_data_white.set_bold()
    #     style_specification_data_white.set_text_wrap()
    #     style_specification_data_white.set_align('left')
    #     style_specification_data_white.set_border()
    #
    #     style_maintenance_majenta = workbook.add_format({})
    #     style_maintenance_majenta.set_fg_color('#F7D6D0')
    #     style_maintenance_majenta.set_font_name('Times New Roman')
    #     style_maintenance_majenta.set_bold()
    #     style_maintenance_majenta.set_text_wrap()
    #     style_maintenance_majenta.set_align('left')
    #     style_maintenance_majenta.set_border()
    #
    #     style_specifications_majenta = workbook.add_format()
    #     style_specifications_majenta.set_fg_color('#F7D6D0')
    #     style_specifications_majenta.set_font_name('Times New Roman')
    #     style_specifications_majenta.set_bold()
    #     style_specifications_majenta.set_text_wrap()
    #     style_specifications_majenta.set_align('left')
    #     style_specifications_majenta.set_border()
    #
    #     style_specifications_white = workbook.add_format()
    #     style_specifications_white.set_fg_color('white')
    #     style_specifications_white.set_font_name('Times New Roman')
    #     style_specifications_white.set_bold()
    #     style_specifications_white.set_text_wrap()
    #     style_specifications_white.set_align('left')
    #     style_specifications_white.set_border()
    #
    #     style_specifications_white_center = workbook.add_format()
    #     style_specifications_white_center.set_fg_color('white')
    #     style_specifications_white_center.set_font_name('Times New Roman')
    #     style_specifications_white_center.set_bold()
    #     style_specifications_white_center.set_text_wrap()
    #     style_specifications_white_center.set_align('center')
    #     style_specifications_white_center.set_border()
    #
    #     style_specifications_yellow = workbook.add_format()
    #     style_specifications_yellow.set_fg_color('#ffff94')
    #     style_specifications_yellow.set_font_name('Times New Roman')
    #     style_specifications_yellow.set_bold()
    #     style_specifications_yellow.set_text_wrap()
    #     style_specifications_yellow.set_align('left')
    #     style_specifications_yellow.set_border()
    #
    #     style_specifications_green = workbook.add_format()
    #     style_specifications_green.set_fg_color('#96e281')
    #     style_specifications_green.set_font_name('Times New Roman')
    #     style_specifications_green.set_bold()
    #     style_specifications_green.set_text_wrap()
    #     style_specifications_green.set_align('left')
    #     style_specifications_green.set_border()
    #     # Add formatting for cells in Excel
    #     # ... (existing code for defining styles)
    #
    #     date_start = data['date_start']
    #     date_end = data['date_end']
    #     type = data['type']
    #     location_id = data['location_id']
    #
    #     if type == 'product':
    #         internal_picking = self.env['stock.picking.type'].search(
    #             [('code', '=', 'internal'), ('sequence_code', '=', 'INT'), ('company_id', '=', self.env.company.id)])
    #
    #         existing_ids = []
    #         move_ids = self.env['stock.move'].search(
    #             [('state', '=', 'done'), ('date', '<=', date_end), ('date', '>=', date_start),
    #              ('picking_type_id', '!=', internal_picking.id), ('company_id', '=', self.env.company.id), '|',
    #              ('location_id', '=', location_id), ('location_dest_id', '=', location_id)
    #              ], order='date asc')
    #
    #         sheet = workbook.add_worksheet()
    #         row = 1
    #         right_row = 3  # For login details
    #         col = 0
    #         sheet.merge_range(row + 1, col, row, col + 10, 'IN OUT LEDGER (PRODUCT BASED)',
    #                           style_specifications_white_center)
    #         row += 2
    #         sheet.merge_range(row + 1, col, row, col + 4, self.env.user.company_id.name, style_specification_data_white)
    #         row += 2
    #         sheet.merge_range(row + 1, col, row, col + 4, "PO BOX : " + str(self.env.user.company_id.zip) + ", " +
    #                           str(self.env.user.company_id.state_id.name) + ", " +
    #                           str(self.env.user.company_id.country_id.name), style_specification_data_white)
    #         row += 3
    #         sheet.merge_range(right_row + 1, col + 6, right_row, col + 10,
    #                           "Period From : " + date_start + " To " + date_end,
    #                           style_specification_data_white)
    #         row += 2
    #         right_row += 2
    #         sheet.merge_range(right_row + 1, col + 6, right_row, col + 10, "Login ID : " + self.env.user.name,
    #                           style_specification_data_white)
    #         right_row += 2
    #         sheet.merge_range(right_row + 1, col + 6, right_row, col + 10, "Location : " + location_id,
    #                           style_specification_data_white)
    #
    #         # Calculate opening balance
    #         opening_balance = in_qty_balance - out_qty_balance
    #
    #         sheet.write(row, col + 10, f"{opening_balance:.2f}", style_specification_data_white)
    #         row += 1
    #
    #         for each in move_ids:
    #             if each.id not in existing_ids:
    #                 existing_ids.append(each.id)
    #                 check_product = []
    #                 product_move_ids = self.env['stock.move'].search(
    #                     [('state', '=', 'done'),
    #                      ('product_id', '=', each.product_id.id), ('date', '<=', date_end),
    #                      ('date', '>=', date_start), ('picking_type_id', '!=', internal_picking.id),
    #                      ('company_id', '=', self.env.company.id),
    #                      '|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)],
    #                     order='date asc')
    #
    #                 balance = 0
    #                 in_qty_balance = 0
    #                 out_qty_balance = 0
    #
    #                 for product_move_id in product_move_ids:
    #                     if product_move_id.location_id.id == location_id:
    #                         if product_move_id.picking_id.location_dest_id.usage == 'internal':
    #                             balance += product_move_id.product_qty
    #                             in_qty_balance += product_move_id.product_qty
    #                             out_qty_balance += 0
    #                         else:
    #                             balance -= product_move_id.product_qty
    #                             out_qty_balance += product_move_id.product_qty
    #                             in_qty_balance += 0
    #
    #                 # Write product details to the worksheet
    #                 sheet.write(row, col, each.product_id.name, style_specification_data_white)
    #                 sheet.write(row, col + 1, each.product_id.default_code or '', style_specification_data_white)
    #                 sheet.write(row, col + 2, each.product_id.uom_id.name or '', style_specification_data_white)
    #                 sheet.write(row, col + 3, each.product_id.categ_id.name or '', style_specification_data_white)
    #                 sheet.write(row, col + 4, each.product_id.barcode or '', style_specification_data_white)
    #                 sheet.write(row, col + 5, in_qty_balance, style_specification_data_white)
    #                 sheet.write(row, col + 6, out_qty_balance, style_specification_data_white)
    #                 sheet.write(row, col + 7, balance, style_specification_data_white)
    #                 sheet.write(row, col + 8, each.date, style_specification_data_white)
    #                 sheet.write(row, col + 9, each.date, style_specification_data_white)
    #                 sheet.write(row, col + 10, each.date, style_specification_data_white)
    #                 row += 1
    #
    #     workbook.close()
    #     output.seek(0)
    #     response.stream.write(output.read())
    #     output.close()
    #
    #     return response

