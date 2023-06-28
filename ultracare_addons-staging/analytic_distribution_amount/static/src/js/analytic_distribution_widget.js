/** @odoo-module **/
import { registry } from "@web/core/registry";
import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";

export class AnalyticDistributionNumber extends AnalyticDistribution {

    async numberChanged(dist_tag, ev) {
        console.log("DIST_TAG", dist_tag)
        console.log("EV", ev)
        var to_percentage = (this.parse(ev.target.value) / this.props.record.data.price_subtotal) * 100
        dist_tag.percentage = to_percentage
        var value = this.parse(ev.target.value)
        console.log("this.parse(ev.target.value)", value)

        dist_tag.number = this.parse(ev.target.value)
        if (this.remainderByGroup(dist_tag.group_id)) {
            this.setFocusSelector(`#plan_${dist_tag.group_id} .incomplete .o_analytic_account_name`);
        }
        this.autoFill();
    }


}
registry.category("fields").add("analytic_distribution_number", AnalyticDistributionNumber);