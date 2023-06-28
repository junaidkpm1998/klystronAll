# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class MaterialRequisition(models.Model):
    _name = 'material.requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Form to request material'

    def get_my_source_config_value(self):
        config = self.env['ir.config_parameter']
        a = config.sudo().get_param("source_location")
        return int(a)

    def get_my_dest_config_value(self):
        config = self.env['ir.config_parameter']
        a = config.sudo().get_param("dest_location")
        return int(a)

    name = fields.Char()
    source_location_id = fields.Many2one('stock.location', default=get_my_source_config_value)
    dest_location_id = fields.Many2one('stock.location', default=get_my_dest_config_value)
    requisition_date = fields.Date(default=datetime.today())
    requisition_line_ids = fields.One2many('material.requisition.line', 'requisition_id')
    material_req = fields.Many2one('production.planning', "Production Planning")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('approve', 'Approved'),
            ('close', 'Close')
        ],
        required=True, tracking=True, default='draft')

    def compute_transfer_count(self):
        self.transfer_counts = 0
        for order in self:
            order.transfer_counts = 0
            stock_transfer = self.env['stock.picking'].search([('material_req_id', '=', order.id)])
            order.transfer_counts = len(stock_transfer)

    transfer_counts = fields.Integer(compute="compute_transfer_count")

    def view_picking(self):
        """Buttons to show Picking"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        stock_pick = self.env['stock.picking'].search([('material_req_id', '=', self.id)])
        if len(stock_pick) > 0:
            action['domain'] = [('id', 'in', stock_pick.ids)]
        return action

    def action_confirm(self):
        """Button for confirming the request"""
        self.state = 'done'

    def action_approve(self):
        """This will create a internal transfer"""
        picking_id = self.env['stock.picking.type'].search(
            [('default_location_src_id', '=', self.source_location_id.id), ('code', '=', 'internal')])
        if len(picking_id) == 0:
            raise ValidationError('No picking type found for this location')
        else:
            picking = self.env['stock.picking'].create(
                {
                    'location_id': self.source_location_id.id,
                    'picking_type_id': picking_id.id,
                    'location_dest_id': self.dest_location_id.id,
                    'origin': self.name,
                    'material_req_id': self.id,
                    'hide_picking_type': False,
                    'show_operations': True,
                    'show_reserved': True,
                    'immediate_transfer': True,
                })
            for move in self.requisition_line_ids:
                move_line = self.env['stock.move.line'].create(
                    {
                        'product_id': move.product_id.id,
                        'location_id': self.source_location_id.id,
                        'location_dest_id': self.dest_location_id.id,
                        'picking_id': picking.id,
                        'qty_done': move.qty_requested,
                        'product_uom_id': move.uom_id.id,
                    })

        mail_template = self.env.ref("kg_material_requisition.approval_notification_mail_template")
        doc_str = ""
        if mail_template:
            values = mail_template.generate_email(self.id, fields={'subject': 'Material Requisition Approved'})
            user_group = self.env.ref("stock.group_stock_manager")
            email_list = [usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
            to_mail = ",".join(email_list)
            values['email_to'] = to_mail
            values['email_from'] = picking.company_id.email
            msg = "<p>Material Requistion with reference no: " + self.name + " is approved</p>"
            values['body_html'] = msg
            mail_mail_obj = self.env['mail.mail']
            msg_id = mail_mail_obj.create(values)
            if msg_id:
                try:
                    mail_mail_obj.send(msg_id)
                except Exception as e:
                    _logger.info("Material Requisition Approval  Mail error : ", str(e))
        self.state = 'approve'

    def action_close(self):
        """Validating the internal transfer"""
        self.state = 'close'
        stock_pick = self.env['stock.picking'].search([('material_req_id', '=', self.id)])
        if len(stock_pick) != 0:
            if stock_pick.state != 'done':
                stock_pick.button_validate()
            else:
                raise UserError("This transfer is already closed.")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('material.requisition') or _('New')
            res = super(MaterialRequisition, self).create(vals)
            return res


class MaterialRequisitionLine(models.Model):
    _name = 'material.requisition.line'
    _description = 'Request material Line'

    requisition_id = fields.Many2one('material.requisition')
    product_id = fields.Many2one('product.product')
    qty_requested = fields.Float(string='Quantity Requested')
    qty_received = fields.Float(string='Quantity Received')
    uom_id = fields.Many2one('uom.uom')

    @api.onchange('product_id')
    def product_onchange(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    material_req_id = fields.Many2one('material.requisition')
    destination = fields.Many2one('res.country', string='Destination')
    is_validate = fields.Boolean(string='Is Validate', default=False)
    is_invoice = fields.Boolean(string='Is Invoice', default=False)
    invoice_document = fields.Many2one('account.move', string='Invoice Document')

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.picking_type_code == 'outgoing':
            self.is_validate = True
        else:
            self.is_validate = False
        return res

    def kg_create_invoice(self):
        if self.picking_type_code == 'outgoing':
            invoice = self.sale_id._create_invoices()
            invoice.action_post()
            self.is_invoice = True
            self.invoice_document = invoice.id
        else:
            self.is_invoice = False
        self.invoice_document.po_no = self.sale_id.po_reference

def get_line_items(self):
    for data in self:
        tabData = []
        lines = []
        length = len(data.sale_id.invoice_ids.invoice_line_ids)
        list_count = 0
        last = False
        last_lines = 0
        doc = {}
        for index, i in enumerate(range(0, length, 18), start=1):
            list_count = index
            lines.append(data.sale_id.invoice_ids.invoice_line_ids[i:i + 18])
        for index, line in enumerate(lines, start=1):
            if list_count == index:
                last = True
                last_lines = len(line)
            doc = {
                'last_lines': last_lines,
                'last': last,
                'lines': line,
            }
            tabData.append(doc)
        return tabData
