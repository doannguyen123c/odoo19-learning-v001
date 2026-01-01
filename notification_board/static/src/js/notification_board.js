odoo.define('notification_board.notification_board', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    // Notification List Widget
    publicWidget.registry.NotificationList = publicWidget.Widget.extend({
        selector: '.notification-board-container',
        events: {},

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initTooltips();
                self._initPopovers();
            });
        },

        _initTooltips: function () {
            // Initialize tooltips if needed
            if (typeof $.fn.tooltip === 'function') {
                this.$('[data-toggle="tooltip"]').tooltip({
                    trigger: 'hover',
                    placement: 'top'
                });
            }
        },

        _initPopovers: function () {
            // Initialize popovers if needed
            if (typeof $.fn.popover === 'function') {
                this.$('[data-toggle="popover"]').popover();
            }
        },

        // No "mark as read" action here; server side doesn't expose it for this model.
    });

    // Notification Detail Widget
    publicWidget.registry.NotificationDetail = publicWidget.Widget.extend({
        selector: '.notification-detail-container',
        events: {},

        start: function () {
            return this._super.apply(this, arguments).then(function () {
                // Any initialization for the detail view
            });
        }
    });

    // Initialize the widgets when the page loads
    return {
        NotificationList: publicWidget.registry.NotificationList,
        NotificationDetail: publicWidget.registry.NotificationDetail
    };
});
