# -*- coding: utf-8 -*-
# /######################################################################################
#
#    Klystron Technologies
#    Copyright (C) 2004-TODAY Klystron Technologies Pvt Ltd.(<http://klystrontech.com/>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# /######################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError

class ChangeWarehouseWizard(models.TransientModel):
    _name = 'change.warehouse.wizard'
    _description = 'Change Warehouse Wizard'

    warehouse_id = fields.Many2one('stock.warehouse','Warehouse')

    def change_warehouse(self):
        for rec in self:
            current_id = self.env.context.get('active_ids')
            obj = self.env['stock.picking'].browse(current_id)

            if obj:
                if obj.picking_type_id.warehouse_id.id == rec.warehouse_id.id:
                    raise UserError(_('Please Select Different Warehouse.'))
                else:
                    new_warehouse = rec.warehouse_id.id
                    code = obj.picking_type_code
                    new_picking = self.env['stock.picking.type'].search([('warehouse_id','=',new_warehouse),('code','=',code)],limit=1)
                    obj.picking_type_id = new_picking
                    if code == 'outgoing':
                        obj.sale_id.warehouse_id = new_warehouse
                        if new_picking.default_location_src_id:
                            obj.location_id = new_picking.default_location_src_id.id
                    elif code == 'incoming':
                        if new_picking.default_location_dest_id:
                            obj.location_dest_id = new_picking.default_location_dest_id.id

                    obj.do_unreserve()
                    obj.action_assign()






