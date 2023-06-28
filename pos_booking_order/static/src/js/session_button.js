odoo.define('pos_booking_order.BookingButton', function (require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { identifyError } = require('point_of_sale.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    class BookingButton extends PosComponent {

        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
        async onClick() {
            //     console.log("juniiiiiiii",)
            //     console.log(this.env.pos.get_order().partner)
            //     console.log("data", this.env.pos.get_order().orderlines)
            if (!this.env.pos.get_order().partner) {
                this.showPopup("ConfirmPopup", {
                    title: this.env._t('Please select the customer'),
                    body: this.env._t('you need tgo select select a customer for booking order'),
                });
            }
            else if (this.env.pos.get_order().orderlines.length == 0) {
                this.showPopup("ConfirmPopup", {
                    title: this.env._t('Please select products'),
                    body: this.env._t('you need tgo select select at least one product'),
                });
            }
            else {

                this.showPopup("popup_widget");
            }



        }
    }
    BookingButton.template = 'BookingButton';
    ProductScreen.addControlButton({
        component: BookingButton,
        condition: function () {
            if (this.env.pos.config.booking_order) {
                return this.env.pos;
            }

        },
    });
    Registries.Component.add(BookingButton);
    return BookingButton;

});