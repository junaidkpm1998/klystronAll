odoo.define('kg_ultracare_sale.form_renderer', function (require) {
"use strict";
var FormRenderer = require('web.FormRenderer');
var core = require('web.core');

var qweb = core.qweb;

FormRenderer.include({

    _updateView: function ($newContent) {
        this._super.apply(this, arguments);
        var $orderLineInfo = this.$el.find('.order_line_info');
        var $chatterContainerMain = this.$el.find('.o_FormRenderer_chatterContainer');
        var $chatterContainer = this.$el.find('.o_ChatterContainer');
        var $statusBar = this.$el.find('.o_form_statusbar');
        var $activityButton = $chatterContainer.find('.o_ChatterTopbar_buttonScheduleActivity')
        $chatterContainerMain.removeClass('order_line_box');
        if (this.state.model === 'sale.order' && $orderLineInfo) {
             if (this._isChatterAside()) {
                $orderLineInfo.insertBefore($chatterContainer);
                $chatterContainerMain.addClass('order_line_box');
            } else {
                $orderLineInfo.insertAfter($statusBar);
            }
         }
    },

});


});