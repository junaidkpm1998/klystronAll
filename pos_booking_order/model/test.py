from odoo import api, models, fields


@api.model


def create_book_order(self, partner_id, phone, pricelist, today, lines, note, pickup_date, deliver_date,
                      delivery_address):
    print("lines", lines)
    values = []
    for l in lines:
        val = {'product_id': l['product_id'],
               'qty': l['qty'],
               'discount': l['discount'],
               'tax_ids': l['taxes_id']
               }
        values.append((0, 0, val))

    order = self.create({
        'partner_id': partner_id,
        'phone': phone,
        # 'delivery_address': delivery_address,
        'pricelist_id': pricelist,
        'date_quotation': today,
        'booking_order': True,
        'order_ids': values,
        'note': note,
    })
    if pickup_date:
        order.write({'pickup_date': pickup_date})
    if deliver_date:
        order.write({'deliver_date': deliver_date,
                     'delivery_address': delivery_address,
                     })
    print('order----->', order)

    # if pickup_date != False:
    #     order_id = self.create({
    #         'partner_id': partner_id,
    #         'order_date': today,
    #         'pickup_date': pickup_date,
    #         'booking_order': True,
    #         'pricelist_id': pricelist,
    #         # 'deliver_date': deliver_date,
    #         # 'delivery_address': delivery_address,
    #         'phone': phone,
    #         'note': note,
    #         'order_ids': values
    #
    #     })
    # # else:
    # #     order_id = self.create({
    # #
    # #
    # #     })
    # return order_id
