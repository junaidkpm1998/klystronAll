from odoo import models, fields, api
from datetime import date
import datetime



class TravelManagement(models.Model):
    _name = 'travel.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Travel Management Model'
    name = fields.Char(string='Sequence Number', readonly=True, default=lambda self: "New")

    customer_id = fields.Many2one('res.partner', required=True)
    no_passengers = fields.Integer(default=1)
    # service = fields.Selection([('flight', 'Flight'), ('train', 'Train'), ('bus', 'Bus')], string="Service",
    #                            required=True)
    service_id = fields.Many2one('tm.service.types', )
    booking_date = fields.Date(string="Date", default=date.today(), readonly=True)
    expiration_date = fields.Date(compute='compute_exp_date', string="Service Expiry Date")
    source_location_id = fields.Many2one('res.country', string="Source Location", required=True)
    dest_location_id = fields.Many2one('res.country', string="Destination Location", required=True)
    date = fields.Datetime(required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('expired', 'Expired')], default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'travel.management') or 'New'
        res = super(TravelManagement, self).create(vals)
        return res

    def to_confirm(self):
        self.write({
            'state': 'confirm',
        })

    def compute_exp_date(self):
        self.expiration_date = self.booking_date + datetime.timedelta(days=self.service_id.expiry_period)
        if self.expiration_date < self.booking_date:
            self.write({
                'state': 'expired'
            })
        # return self.expiration_date



    # @api.onchange('expiration_date')
    # def onchange_expiration_date(self):
    #     print(self.expiration_date)
    #     print(type(self.expiration_date),"expiration_date")
    #     print(type(self.booking_date),"booking_date")
        # if self.expiration_date > self.booking_date:
        #     print("yess")
            # self.write({
            #     'state': 'expired'
            #
            # })
