odoo.define('point_of_sale.popup_widget', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _lt } = require('web.core'); const { parse } = require('web.field_utils');
    var rpc = require('web.rpc')
    var models = require('point_of_sale.models');
    const { _t } = require('@web/core/l10n/translation');
    class popup_widget extends AbstractAwaitablePopup {
    setup(){
        super.setup()
        this.order = this.env.pos.selectedOrder
        console.log('this.order-------',this.order)
     }
      confirm() {
            var pickup_date = $('#pickup').val();
            var deliver_date =  $('#deliver').val();
            var note = $('.order_note').val()
            var partner_id = this.order.partner.id
            var delivery_address = $('#delivery_address').val()
            var phone = $('#phone').val()
            var today = new Date().toJSON().slice(0, 10)
            var pricelist = this.order.pricelist.id;
            console.log('pricelist',pricelist)
            var orderline = this.order.orderlines
            var lines = []
            for (var line in orderline) {
                var values = {
                    'product_id': orderline[line]['product']['id'],
                    'qty': orderline[line]['quantity'],
                    'discount': orderline[line]['discount'],
                    'taxes_id':orderline[line]['product']['taxes_id'] || false
                }
                lines.push(values)

            }
            console.log(partner_id,"partner_id")
            console.log('line', lines)

            if (!pickup_date && !deliver_date) {
                this.showPopup('ErrorPopup', {
                    'title': _t('Date field is empty'),
                    'body': _t('Please select pickup or deliver date!!'),
                });
            }
            else if (pickup_date && deliver_date) {
                this.showPopup('ErrorPopup', {
                    'title': _t('Select only one date'),
                    'body': _t('Select only one date (Deliver or Pickup date)'),
                });
            }
            else if (pickup_date) {
                if (pickup_date < today) {
                    this.showPopup('ErrorPopup', {
                        'title': _t('Please Select Valid Pickup Date!'),
                        'body': _t('Date must be greater than today'),
                    });
                }
                else {
                    rpc.query({
                        model: 'booking.order',
                        method: 'create_book_order',
                        args: [partner_id, phone, pricelist, today, lines, note, pickup_date, deliver_date,
                          delivery_address],
//                        args: [partner_id],
                    })
                        .then(function (order) {
                            console.log('order', order)
                            //
                        })
                    this.env.pos.add_new_order()
//                    document.location.reload()


                }
            }
            else {
                if (deliver_date < today) {
                    this.showPopup('ErrorPopup', {
                        'title': _t('Please Select Valid Deliver Date!'),
                        'body': _t('Date must be greater than today'),
                    });
                }
                else {
                    rpc.query({
                        model: 'booking.order',
                        method: 'create_book_order',
                        args: [partner_id],
                    })
                        .then(function (order) {
                            console.log('order', order)

                        });
                    this.env.pos.add_new_order()
                }
            }
            return super.confirm();
      }

    }

popup_widget.template = 'popup_widget';

Registries.Component.add(popup_widget);
return popup_widget;

});