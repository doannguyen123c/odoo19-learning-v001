odoo.define('notification_board.notification_board', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;

    // Notification List Widget
    publicWidget.registry.NotificationList = publicWidget.Widget.extend({
        selector: '.notification-board-container',
        events: {
            'click .mark-as-read': '_onMarkAsRead',
        },

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

        _onMarkAsRead: function (ev) {
            ev.preventDefault();
            var $target = $(ev.currentTarget);
            var notificationId = $target.data('notification-id');
            
            // Show loading state
            $target.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> ' + _t('Đang đánh dấu...'));
            
            // Call the server to mark as read
            this._rpc({
                model: 'notification.board',
                method: 'set_message_done',
                args: [[parseInt(notificationId)]],
            }).then(function () {
                // Remove the notification from the list
                $target.closest('.notification-item').fadeOut(300, function() {
                    $(this).remove();
                });
            }).guardedCatch(function (error) {
                console.error('Lỗi khi đánh dấu đã đọc:', error);
                $target.prop('disabled', false).text(_t('Đánh dấu đã đọc'));
            });
        },
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
