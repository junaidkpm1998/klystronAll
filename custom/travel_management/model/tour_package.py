from odoo import models, fields, api


class TmServiceTypes(models.Model):
    _name = 'tour.package'
    _rec_name = 'customer_id'

    customer_id = fields.Many2one('res.partner', required=True)
    quotation_date = fields.Date(required=True)
    source_location = fields.Many2one('res.country', required=True)
    dest_location = fields.Many2one('res.country', required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    no_of_travellers = fields.Integer(default=1)
    facilities = fields.Many2many('vehicle.facilities')
    vehicle_typesa = fields.Selection([('bus', 'BUS'), ('traveller', 'TRAVELLER'), ('van', 'VAN'), ('other', 'OTHER')],
                                      required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed')], default='draft')
    estimation = fields.One2many('tm.estimation', 'estimation')
    # total = fields.Integer(related='estimation.total_amount')
    total_amount = fields.Integer(compute='total_amount_compute')
    vehicle = fields.Many2one('tm.vehicle')

    def total_amount_compute(self):
        self.total_amount = sum(self.estimation.mapped('sub_total'))

    @api.onchange('start_date', 'end_date', 'no_of_travellers', 'facilities', 'vehicle_typesa')
    def vehicle_name(self):
        for rec in self:
            bookings = rec.search([
                ('start_date', '<', rec.end_date),
                ('end_date', '>', rec.start_date),
            ])
            vehicle_ids = bookings.mapped('vehicle')
            if rec.facilities:
                return {
                    'domain': {'vehicle': [
                        ('id', 'not in', vehicle_ids.ids),
                        ('facilities', 'in', rec.facilities.ids),
                        ('vehicle_types', 'like', rec.vehicle_typesa),
                        ('no_seat', '>=', rec.no_of_travellers),
                    ],
                    }
                }
            else:
                return {
                    'domain': {'vehicle': [
                        ('id', 'not in', vehicle_ids.ids),
                        ('vehicle_types', 'like', rec.vehicle_typesa),
                        ('no_seat', '>', rec.no_of_travellers),
                    ],
                    }
                }

    # @api.onchange('vehicle_typesa', 'no_of_travellers', 'facilities')
    # def onchange_vehicle_typesa(self):
    #     for rec in self:
    #
    #         if rec.vehicle_typesa or rec.no_of_travellers or rec.facilities:
    #             domain = {'vehicle': [('vehicle_types', '=', rec.vehicle_typesa), ('no_seat', '>', rec.no_of_travellers),
    #                                   ('facilities', 'in', rec.facilities.ids)]}
    #             return {'domain': domain}
    #
    #     # if self.no_of_travellers:
    #     #     domain = {'vehicle': [('no_seat', '>', self.no_of_travellers)]}
    #
    # # @api.onchange('no_of_travellers')
    # # def onchange_no_of_travellers(self):
    # #     domain = {'vehicle': [('no_seat', '>', self.no_of_travellers)]}
    # #     return {'domain': domain}
