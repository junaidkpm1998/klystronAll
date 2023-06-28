odoo.define('pos_booking_order.BookedButton', function(require) {
'use strict';
  const { Gui } = require('point_of_sale.Gui');
  const PosComponent = require('point_of_sale.PosComponent');
  const { identifyError } = require('point_of_sale.utils');
  const ProductScreen = require('point_of_sale.ProductScreen');
  const { useListener } = require("@web/core/utils/hooks");
  const Registries = require('point_of_sale.Registries');
  const PaymentScreen = require('point_of_sale.PaymentScreen');
  class BookedButton extends PosComponent {
      setup() {
          super.setup();
          useListener('click', this.onClick);
      }
     async onClick() {

     this.showScreen('BookedOrdersWidget');

                 }
  }
BookedButton.template = 'BookedButton';
  ProductScreen.addControlButton({
      component: BookedButton,
      condition: function() {
            if (this.env.pos.config.booking_order) {
                     return this.env.pos;
       }

      },
  });
  Registries.Component.add(BookedButton);
  return BookedButton;
});