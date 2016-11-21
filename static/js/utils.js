// Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
// License: MIT, see LICENSE for more details.

if (!Skylable_Utils) {
    /**
     * Various utility functions.
     * 
     * @type {{removeRootFromPath: Function, getRootFromPath: Function, slashPath: Function, basename: Function}}
     */
    var Skylable_Utils = {
        /**
         * Remove the first part of a path.
         * @param path
         * @returns {string}
         */
        removeRootFromPath : function(path) {
            if (path.length == 0) {
                return '/';
            }

            var p = path.indexOf('/', path.indexOf('/') + 1);
            if (p < 0) {
                return '/';
            } else {
                return path.substring(p);
            }
        },

        /**
         * Returns the root from a path
         * @param path
         * @returns {string}
         */
        getRootFromPath : function(path) {
            if (path.length == 0) {
                return '';
            }

            var p1 = path.indexOf('/');
            if (p1 < 0) {
                return path;
            } else if (p1 > 0) {
                return path.substring(0, p1);
            } else {
                var p2 = path.indexOf('/', p1 + 1);
                if (p2 < 0) {
                    return path.substring(p1 + 1);
                } else {
                    return path.substring(p1 + 1, p2);
                }
            }
        },

        /**
         * Add a slash to the beginning part of a path
         * @param {string} path
         * @returns {string}
         */
        slashPath : function(path) {
            if (path.length == 0) {
                return '/';
            }
            var p1 = path.indexOf('/');
            if (p1 > 0) {
                return '/' + path;
            }
            return path;
        },

        /**
         * Returns the last part of a path
         * @param path
         * @returns {string}
         */
        basename : function(path) {
            if (path.length == 0) {
                return '';
            }
            var p = path.lastIndexOf('/');
            if (p == path.length - 1) {
                p--;
                p = path.lastIndexOf('/', p);
            }
            if (p != -1) {
                return path.substring(++p, path.length);
            }
            return path;
        },

        /**
         * Trim a string to a given length and adds trailing '...'. 
         * @param str
         * @param length
         * @returns {string}
         */
        trs : function (str, length) {
            return (str.length > (length - 3) ? str.substring(0, length - 3) + '...' : str);
        },

        /**
         * Convert NL chars to HTML break 
         * @param str
         * @returns {XML|string|void|*}
         */
        nl2br : function (str) {
            return str.replace(/(?:\r\n|\r|\n)/g, '<br />');
        },

        /**
         * Trim a string to a given size, removing chars from the center and adding '...'
         * IE: "big string with a lot of text" became "big...text" when trimmed to 10 chars.
         * @param string str
         * @param integer length desired length
         * @returns {*}
         */
        trim_str_center: function(str, length) {
            if ((str.length > length) && (length > 0)) {
                return str.substring(0, (length - 3) / 2) + '...' + str.substring(str.length - (length - 3) / 2); 
            } else {
                return str;
            }
        },

        /**
         * Return the default dialog window witdh.
         * 
         * @returns {*}
         */
        defaultDialogWidth : function() {
            var ww = $(window).width();

            if (ww < 800) {
                return (ww - 20);
            } else if (ww > 1024) {
                return 700;
            } else {
                return ((ww * 2) / 3);
            }
            
        }
    }
}
