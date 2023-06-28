odoo.define('pos_a4_print.InvoicePrint', function (require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { identifyError } = require('point_of_sale.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    class InvoicePrint extends PosComponent {

           setup() {
               super.setup();
               useListener('click', this.InvoicePrint);
           }
           InvoicePrint() {
              // click_invoice
              Gui.showPopup("ConfirmPopup", {
                      title: this.env._t('Title'),
                      body: this.env._t('Welcome to OWL(body of popup)'),
                  });
          }
    }
    InvoicePrint.template = 'InvoicePrint';
    Registries.Component.add(InvoicePrint);
    return InvoicePrint;

});