odoo.define('spa_management.SpaDashboard', function (require) {
    "use strict";
    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const rpc = require("web.rpc");
    var ajax = require("web.ajax");
    var session = require('web.session');
    const _t = core._t;
    const QWeb = core.qweb;
    const SpaDashboard = AbstractAction.extend({
        template: 'SpaDashboardMain',
        events: {
            'click .spa_spa_bookings': 'bookings',
            'click .spa_spa_bookings_today': 'bookings_today',
            'click .spa_spa_sales': 'sales',
            'click .spa_spa_clients': 'clients',
            'click .spa_spa_orders': 'orders',
            'click .spa_chair': 'chairs_click',
            'click .chair_setting': 'settings_click'
        },
        init: function (parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['SpaSpaDashBoard'];

        },

        start: function () {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.render_dashboards();
                self.$el.parent().addClass('oe_background_grey');
            });

        },
        render_dashboards: function () {
            var self = this;
            var templates = ['SpaSpaDashBoard'];
            _.each(templates, function (template) {
                self.$('.spa_spa_dashboard').append(QWeb.render(template, {widget: self}));
            });
            rpc.query({
                model: "spa.booking",
                method: "get_booking_count",
                args: [{"company_ids" : session.user_context.allowed_company_ids}],
            })
                .then(function (result) {
                    $("#bookings_count").append("<span class='stat-digit'>" + result.bookings + "</span>");
                    $("#bookings_today_count").append("<span class='stat-digit'>" + result.bookings_today + "</span>");
                    $("#recent_count").append("<span class='stat-digit'>" + result.sales + "</span>");
                    $("#orders_count").append("<span class='stat-digit'>" + result.orders + "</span>");
                    $("#clients_count").append("<span class='stat-digit'>" + result.clients + "</span>");
                    // console.log("pass to controller");
                    // Hide displaying chair on Dashboard
                    //ajax.jsonRpc("/spa/chairs", "call", {}).then(function (values) {
                    //    $('#chairs_dashboard_view').append(values);
                    //});
                });
        },
        on_reverse_breadcrumb: function () {
            var self = this;
            self.$('.spa_spa_dashboard').empty();
            self.render_dashboards();
        },

        //events
        chairs_click: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            var active_id = event.target.id
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Chair Orders"),
                type: 'ir.actions.act_window',
                res_model: 'sale.order',
                view_mode: 'kanban,tree,form',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                domain: [['chair_id', '=', parseInt(active_id)]],
                context: {
                    default_chair_id: parseInt(active_id)
                },
                target: 'current'
            }, options);
        },

        settings_click: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            var active_id = event.target.id
            console.log(active_id,"acname")
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Chair Orders"),
                type: 'ir.actions.act_window',
                res_model: 'spa.chair',
                view_mode: 'form',
                views: [[false, 'form']],
                context: {
                    default_name: active_id
                },
                target: 'current'
            }, options);
        },


        bookings: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

            this.do_action({
                name: _t("Bookings"),
                type: 'ir.actions.act_window',
                res_model: 'spa.booking',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', 'in', ['draft', 'confirmed']], ['company_id', 'in', session.user_context.allowed_company_ids]],
                target: 'current'
            }, options);
        },

        bookings_today: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            const start_date = new Date();
            // Reset a Date's time to midnight
            start_date.setHours(0, 0, 0, 0);

            const end_date = new Date();
            // Reset a Date's time to midnight
            end_date.setHours(23, 59, 59, 0);
    
            //const dateFormat = `${year}-${month}-${day}`;
            const start_utc = Date.UTC(start_date.getUTCFullYear(), start_date.getUTCMonth(), start_date.getUTCDate(), start_date.getUTCHours(),
                            start_date.getUTCMinutes(), start_date.getUTCSeconds());
            const end_utc = Date.UTC(end_date.getUTCFullYear(), end_date.getUTCMonth(), end_date.getUTCDate(), end_date.getUTCHours(),
                            end_date.getUTCMinutes(), end_date.getUTCSeconds());
            
            const start_dt_utc =  new Date(start_utc);
            const end_dt_utc =  new Date(end_utc);

            console.log("start_dt_utc: "+start_dt_utc + "=>" + end_dt_utc);
            // click Today's booking, go to the calendar current day view
            this.do_action({
                name: _t("Today's Bookings"),
                type: 'ir.actions.act_window',
                res_model: 'spa.booking',
                view_mode: 'calendar',
                views: [[false, 'calendar'], [false, 'list'], [false, 'form']],
                domain: [
                    ['company_id', 'in', session.user_context.allowed_company_ids]
                ],
                target: 'current'
            }, options);
        },

        sales: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

            // stage_id = 3(Invoiced), 4(Closed)
            this.do_action({
                name: _t("Sales"),
                type: 'ir.actions.act_window',
                res_model: 'sale.order',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', 'in', ['sale','done']],['company_id', 'in', session.user_context.allowed_company_ids]],
                target: 'current'
            }, options);
        },
        orders: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

            this.do_action({
                name: _t("Total Orders"),
                type: 'ir.actions.act_window',
                res_model: 'sale.order',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                domain: [['company_id', 'in', session.user_context.allowed_company_ids]],
                target: 'current'
            }, options);
        },
        clients: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
            };
            self.do_action({
                name: _t("Clients"),
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['partner_spa', '=', true]],
                target: 'current'
            }, options);
        },


    });
    core.action_registry.add('spa_dashboard', SpaDashboard);
    return SpaDashboard;
});
