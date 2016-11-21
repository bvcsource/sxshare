// Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
// License: MIT, see LICENSE for more details.

if (!FileOperations) {
    /**
     * Handles all the files operations.
     *
     * In the global scope should be defined a variable named 'current_path' with
     * the current visited path.
     *
     * @constructor
     */
    var FileOperations = {
        urls: {
            create_dir:"/create_dir",
            file_list: "/filelist",
            copy_files: "/copy",
            move_files: "/move",
            delete_files: "/delete",
            window: "/ajax/vol",
            rename_files : '/rename',
            share_file : '/share'
        },
        self: this,

        // Flag
        is_working: false,

        /**
         * Returns the progress bar HTML
         * @param message message key to show into the progress bar
         * @returns {string}
         */
        getProgressBarHTML : function(message) {
            return '<div id="prog"><div class="progress-label">'+ Skylable_Lang[message] +'</div></div>';
        },

        /**
         * Copy files, used in event handlers
         * @param event
         * @returns {*}
         */
        copy : function (event) {
            return FileOperations.copyMove(event, false);
        },

        /**
         * Move files, used in event handlers
         * @param event
         * @returns {*}
         */
        move : function (event) {
            return FileOperations.copyMove(event, true);
        },

        // Source directory
        source_dir : '',

        // Destination directory
        dest_dir : '',

        // List of file paths
        files : [],

        /**
         * Populate the list of selected files
         */
        getSelectedFiles : function() {
            // get the file list
            FileOperations.files = [];
            $('input:checkbox[name=file_element]:checked').each(function(){
                FileOperations.files.push( $(this).val() );
            });
        },

        /**
         * Copies or move files.
         *
         * @param event
         * @param bool move true move files, false copy
         */
        copyMove : function(event, move) {
            FileOperations.is_working = false;
            var dlg = FileOperations.getDialog( (move ? Skylable_Lang["moveTitle"] : Skylable_Lang["copyTitle"]) );

            FileOperations.getSelectedFiles();

            dlg.dialog('option', 'buttons', [
                    {
                        id: 'action_btn',
                        text: (move ? Skylable_Lang["moveBtn"] : Skylable_Lang["copyBtn"]),
                        click: function() {

                            FileOperations.dest_dir = $(dlg).find('#index_ajax_vols').val() + Skylable_Utils.slashPath( $(dlg).find('#index_ajax_patch').val()) ;
                            
                            console.log('From: ' + FileOperations.source_dir);
                            console.log('To: ' + FileOperations.dest_dir);

                            var f = '';
                            for(elem in FileOperations.files) {
                                f += '&files[]='+encodeURIComponent( FileOperations.files[elem] );
                            }

                            dlg.html(FileOperations.getProgressBarHTML('working'));
                            var progressbar = $('#prog');

                            $(progressbar).progressbar({
                                max: 100,
                                value: 0,
                                enable: true
                            });

                            $(progressbar).progressbar("option", "value", 25);

                            $.ajax({
                                url : (move ? FileOperations.urls.move_files : FileOperations.urls.copy_files ),
                                data: 'dest='+encodeURIComponent( FileOperations.dest_dir )+f,
                                method : 'POST',
                                beforeSend : function(xhr, options) {
                                    FileOperations.is_working = true;
                                    $('#action_btn').button('disable');
                                },
                                success: function(data, status, xhr) {
                                    $('#action_btn').hide();
                                    $(progressbar).progressbar("option", "value", 75);
                                    FileOperations.updateFileList();
                                    $(dlg).html(data);
                                },
                                error : function(xhr, status) {
                                    if (!FileOperations.expiredUser(dlg, xhr)) {
                                        $('#action_btn').hide();
                                        dlg.html(xhr.responseText);
                                    }
                                },
                                complete : function(xhr, status) {
                                    FileOperations.is_working = false;        
                                }
                            });
                            
                        }
                    },
                    {
                        text: Skylable_Lang["close"],
                        click: function() {
                            $(this).dialog("close");
                            $(this).dialog("destroy");
                        }
                    }
                ] );

            if (FileOperations.files.length > 0) {
                // Important: Don't encode the source dir, but encodes the destination
                FileOperations.populateCopyMoveWindow(dlg, current_path, encodeURI(current_path) );
            } else {
                $('#action_btn').hide();
                dlg.html('<p>' + Skylable_Lang['noFilesSelected'] + '</p>');
                dlg.dialog("open");
            }

            event.preventDefault();
        },

        /**
         * Populate a jQuery UI window with a file selector.
         *
         * @param dialog jQuery UI dialog
         * @param source_dir the source must be the plain path
         * @param dest_dir the destination dir must be an encoded URI
         */
        populateCopyMoveWindow : function(dialog, source_dir, dest_dir) {
            FileOperations.source_dir = source_dir;
            FileOperations.dest_dir = dest_dir;

            dialog.html(FileOperations.getProgressBarHTML('working'));
            var progressbar = $('#prog');

            $(progressbar).progressbar({
                max: 100,
                value: 0,
                enable: true
            });

            $(progressbar).progressbar("option", "value", 25);

            // $('#action_btn').hide();
            dialog.dialog("open");

            $.ajax({
                url:FileOperations.urls.window + dest_dir,
                method : "GET",
                beforeSend: function(xhr, options) {
                    $(progressbar).progressbar("option", "value", 50);
                    return true;
                },
                success: function(data, status, xhr) {
                    $(progressbar).progressbar("option", "value", 75);
                    $(progressbar).progressbar("enable", false);
                    $(dialog).html(data);
                    $(dialog).children('#index_ajax_from').html(source_dir);
                    $(dialog).find('#index_ajax_patch').val( Skylable_Utils.removeRootFromPath( decodeURI(dest_dir) ) );
                    var index_ajax_list = $(dialog).children('#index_ajax_list');
                    if (source_dir === dest_dir) $(index_ajax_list).hide();
                    $(index_ajax_list).children('li').click(function(){
                        var volume = $(dialog).find('#index_ajax_vols').val();
                        FileOperations.populateCopyMoveWindow(dialog, source_dir, '/' + volume + $(this).attr("url") );
                    });
                    $(dialog).find('#shfiles').click(function(e){
                        $(dialog).children('#index_ajax_list').toggle();
                        e.preventDefault();
                    });
                    var vol_selector = $(dialog).find('#index_ajax_vols');
                    vol_selector.val(Skylable_Utils.getRootFromPath(dest_dir));
                    vol_selector.change(function(){
                        var volume = $(this).val();
                        FileOperations.populateCopyMoveWindow(dialog, source_dir, '/' + volume );
                    });

                    /*
                    if (source_dir !== dest_dir) {
                        $('#action_btn').show();
                    }
                    */
                },
                error : function (xhr, status) {
                    $(progressbar).progressbar("option", "value", 100);
                    if (!FileOperations.expiredUser(dialog, xhr)) {
                        $('#action_btn').hide();
                        dialog.html(xhr.responseText);
                    }
                }
            });
        },

        /**
         * Create a new directory.
         *
         * @param event
         * @returns {boolean}
         */
        createDir : function(event) {
            FileOperations.is_working = false;
            var dlg = FileOperations.getDialog(Skylable_Lang["createDirTitle"]);

            var getCreateDirHTML = function() {
                return '<ul><li>' + Skylable_Lang['createDirNameLabel'] + '<input class="share-file-link createdir" type="text" value="" name="createdir_name" /></li></ul>';
            };

            dlg.dialog('option', 'buttons', [
                    {
                        // The "Create" button
                        id : 'create_dir_action_btn',
                        text: Skylable_Lang["createDirBtn"],
                        click: function(event) {

                            // Hide the "create" button
                            $(event.target).hide();

                            var dir_name_obj = document.getElementsByName('createdir_name').item(0);
                            var dir_name = $.trim(dir_name_obj.value);
                            // Name must be non empty
                            if (dir_name.length > 0) {
                                // Create dir with AJAX
                                $(this).html(FileOperations.getProgressBarHTML('working'));
                                var progressbar = $('#prog');
                                $(progressbar).progressbar({
                                    max: 100,
                                    value: 0,
                                    enable: true
                                });

                                // Create the dir
                                $(progressbar).progressbar("option", "value", 50);
                                $.ajax({
                                    method: "POST",
                                    url : FileOperations.urls.create_dir,
                                    data: "name="+ encodeURIComponent(dir_name)+"&path="+encodeURIComponent(current_path),
                                    beforeSend : function(xhr, options) {
                                        FileOperations.is_working = true;
                                    },
                                    success: function(data, status, xhr) {
                                        FileOperations.is_working = false;
                                        if (xhr.status == 201) { // Can't create the dir
                                            $(progressbar).progressbar("enable", false);
                                            dlg.html(getCreateDirHTML());
                                            $(event.target).show();
                                        } else {
                                            // Update the view
                                            FileOperations.updateFileList(function(s){
                                                $(progressbar).progressbar("option", "value", 100);
                                                dlg.dialog("close");
                                                dlg.dialog("destroy");
                                            });
                                        }
                                    },
                                    error : function (xhr, status) {
                                        $(progressbar).progressbar("option", "value", 100);
                                        if (!FileOperations.expiredUser(dlg, xhr)) {
                                            $('#create_dir_action_btn').hide();
                                            dlg.html(xhr.responseText);
                                        }
                                    },
                                    complete : function(xhr, status) {
                                        FileOperations.is_working = false;        
                                    }
                                });
                                
                            } else {
                                $(event.target).show();
                            }
                        }
                    },
                    {
                        text: Skylable_Lang["close"],
                        click: function() {
                            dlg.dialog("close");
                            dlg.dialog("destroy");
                        }
                    }
                ] );

            dlg.html(getCreateDirHTML());
            dlg.dialog("open");

            event.preventDefault();
        },
        
        uncheckSelectAllControl : function() {
            $('p.table-title span.date input[name=table_title_file_list_select_all]').prop('checked', false);
        },

        /**
         * Updates the file list.
         * 
         * Callback signature is:
         * 
         * callback(status)
         * 
         * where status is a boolean: true successfully updated, false otherwise
         *
         * @returns {boolean} true on success, false on failure
         */
        updateFileList : function(callback) {
            FileOperations.uncheckSelectAllControl();
            var _this = this;
            var _status = false;
            $.ajax({
                type: 'GET',
                url : _this.urls.file_list,
                data : "path=" + encodeURIComponent(current_path),
                dataType : 'html',
                success : function(data,status,xhr){
                    $('#main-file-list').html(data);
                    _status = true;
                    FileOperations.assignFileListHandlers();
                },
                error: function(xhr, status) {

                },
                complete : function(xhr, status) {
                    if (typeof  callback === 'function') {
                        callback(_status);
                    }
                }
            });
            return _status;
        },

        /**
         * Rename a file
         *
         * @param filename the basename of the file to rename
         * @param path the full path of the file to rename
         */
        renameFile : function (filename, path) {
            FileOperations.is_working = false;
            var dlg = FileOperations.getDialog(Skylable_Lang['renameTitle']);
            dlg.dialog("option", 'buttons', [
                        {
                            id : 'dlg_rename_btn',
                            text: Skylable_Lang['renameBtn'],
                            click: function (ev) {
                                var the_new_name = $(dlg).find('input[name=rename_to]').val().trim();

                                if(the_new_name.length > 0) {
                                    $('#dlg_rename_btn').hide();

                                    dlg.html( FileOperations.getProgressBarHTML('working') );
                                    var progressbar = $('#prog');
                                    $(progressbar).progressbar({
                                        max: 100,
                                        value: 25,
                                        enable: true
                                    });
                                    $.ajax({
                                        url : FileOperations.urls.rename_files,
                                        method: 'POST',
                                        data : 'source='+path+'&new_name='+the_new_name,
                                        beforeSend : function(xhr, options) {
                                            $(progressbar).progressbar('option', 'value', 50);
                                            FileOperations.is_working = true;
                                        },
                                        success : function(data, status, xhr) {
                                            $(progressbar).progressbar('option', 'value', 100);
                                            FileOperations.updateFileList(function(s){
                                                dlg.dialog('close');
                                                dlg.dialog("destroy");
                                            });
                                        },
                                        error : function(xhr, status) {
                                            if (!FileOperations.expiredUser(dlg, xhr)) {
                                                dlg.html(xhr.responseText);
                                            }
                                        },
                                        complete : function(xhr, status) {
                                            FileOperations.is_working = false;        
                                        }
                                    });
                                    
                                }
                            }
                        },
                        {
                            text: Skylable_Lang['close'],
                            click : function (ev) {
                                dlg.dialog("close");
                                dlg.dialog("destroy");
                            }
                        }
                    ]
            );
            dlg.html(
                '<ul>'+
                '<li>' + Skylable_Lang['renameFrom'] + '<input class="share-file-link" type="text" readonly="readonly" value="'+filename+'" name="rename_from" /></li>'+
                '<li>' + Skylable_Lang['renameTo'] + '<input class="share-file-link" type="text" value="'+filename+'" name="rename_to" /></li>'+
                '</ul><br/>'
            );
            dlg.dialog("open");
        },

        /**
         * Delete files window
         * @param ev
         */
        deleteFiles : function(ev) {
            FileOperations.is_working = false;
            var dlg = FileOperations.getDialog(Skylable_Lang['deleteTitle']);

            FileOperations.getSelectedFiles();
            if (FileOperations.files.length == 0) {
                dlg.dialog("option", 'buttons', [
                        {
                            text: Skylable_Lang['close'],
                            click : function (ev) {
                                dlg.dialog("close");
                                dlg.dialog("destroy");
                            }
                        }
                    ]
                );
                dlg.html('<p>'+Skylable_Lang['deleteNoFiles']+'</p>');
            } else {
                dlg.html('<p>'+Skylable_Lang['deleteMsg']+'</p>');
                for (idx in FileOperations.files) {
                    FileOperations.files[idx] = 'files[]='+encodeURIComponent( FileOperations.files[idx] );
                }

                dlg.dialog("option", 'buttons', [
                        {
                            id : 'remove_action_btn',
                            text: Skylable_Lang['yes'],
                            click: function (ev) {
                                dlg.dialog("option", 'buttons', [{
                                    text : Skylable_Lang['closeBtn'],
                                    click : function(ev) {
                                        dlg.dialog('close');
                                    }
                                }]);

                                dlg.html(FileOperations.getProgressBarHTML('working'));
                                var progressbar = $('#prog');
                                $(progressbar).progressbar({
                                    max: 100,
                                    value: 25,
                                    enable: true
                                });

                                $.ajax({
                                    url : FileOperations.urls.delete_files,
                                    data : FileOperations.files.join('&'),
                                    method : 'POST',
                                    beforeSend : function(xhr, options) {
                                        FileOperations.is_working = true;
                                    },
                                    success : function(data, status, xhr) {
                                        $(progressbar).progressbar('option', 'value', 75);
                                        FileOperations.updateFileList(function(s){
                                            if (s) {
                                                $(progressbar).progressbar('option', 'value', 100);    
                                            }
                                            dlg.html(xhr.responseText);    
                                        });
                                    },
                                    error : function(xhr, status) {
                                        if (!FileOperations.expiredUser(dlg, xhr)) {
                                            dlg.html(xhr.responseText);
                                        }
                                    },
                                    complete : function(xhr, status) {
                                        FileOperations.is_working = false;        
                                    }
                                });
                                
                            }
                        },
                        {
                            text: Skylable_Lang['no'],
                            click : function (ev) {
                                dlg.dialog("close");
                                dlg.dialog("destroy");
                            }
                        }
                    ]
                );
            }

            dlg.dialog("open");
        },

        /**
         * Assigns all the file list event handlers
         */
        assignFileListHandlers : function() {
            // File operations
            $('#selectable').find('li.ui-widget-content').children('.actions').each(function(){
                $(this).find('.elmcopy').click(function(e){
                    $("#selectable input:checkbox").prop('checked',false);
                    $(this).parent().parent().parent().find('input:checkbox').prop('checked',true);
                    FileOperations.copyMove(e, false);
                });

                $(this).find('.elmmove').click(function(e){
                    $("#selectable input:checkbox").prop('checked',false);
                    $(this).parent().parent().parent().find('input:checkbox').prop('checked',true);
                    FileOperations.copyMove(e, true);
                });

                $(this).find('.elmrename').click(function(e){
                    var name = $(this).parent().parent().parent().find('input:checkbox').val();
                    FileOperations.renameFile(
                        $(this).parent().parent().parent().find('input[name=file_basename]:hidden').val(),
                        $(this).parent().parent().parent().find('input[name=file_element]:checkbox').val()
                    );
                });

                $(this).find('.elmdelete').click(function(e){
                    $("#selectable input:checkbox").prop('checked',false);
                    $(this).parent().parent().parent().find('input:checkbox').prop('checked',true);
                    FileOperations.deleteFiles(e);

                });

                $(this).find('.elmshare').click(function(e){
                    path = $(this).parent().parent().parent().find("input:checkbox[name=file_element]").val()
                    FileOperations.shareFile(e, path);
                });
                
                /*
                $(this).find('.elmpreview').click(function(e){
                    var type = $(this).data('filetype');
                    if (type === 'data') {
                        return true;
                    } else {
                        FileOperations.previewFile($(this).attr('href'), type);
                        e.preventDefault();
                    }
                });
                */
            });

            $('#selectable').find('li.ui-widget-content .elmpreview').click(function(e){
                
                    var type = $(this).data('filetype');
                    if (type === 'data') {
                        return true;
                    } else {
                        FileOperations.previewFile($(this).attr('href'), type);
                        e.preventDefault();
                    }
                
            });

            $("a.actions-trigger" ).click(function() {
                $(this).next().toggleClass("active", 200, 'easeInOutExpo' );
                $(this).toggleClass("active", 200, 'easeInOutExpo' );
            });
        },

        /**
         * Manages an expired user.
         *
         * @param dialog
         * @param xhr
         * @returns {boolean}
         */
        expiredUser : function(dialog, xhr) {
            if (xhr.status === 403) {
                var type = xhr.getResponseHeader('Content-Type');
                if (type === 'application/json') {
                    var data = JSON.parse(xhr.responseText);

                    dialog.html('<p>' + data.error + '</p>');
                    dialog.dialog({
                        buttons:[{
                            text : Skylable_Lang['doLoginBtn'],
                            click : function (e) {
                                window.location.href = data.url;
                            }
                        }]
                    });

                } else {
                    dialog.html(xhr.responseText);
                    dialog.dialog({
                        buttons:[{
                            text : Skylable_Lang['closeBtn'],
                            click : function (e) {
                                FileOperations.is_working = false;
                                dialog.dialog('close');
                                dialog.dialog('destroy');
                            }
                        }]
                    });
                }
                return true;
            }
            return false;
        },

        /**
         * Do the share file action.
         * 
         * @param ev
         * @param path
         */
        shareFile : function(ev, path) {
            var dlg = FileOperations.getDialog(Skylable_Lang['shareTitle']);
            dlg.dialog('option', 'buttons', [
                {
                  text: Skylable_Lang['yesBtn'],
                    click: function(e) {
                        var send_data = 'path='+encodeURIComponent( path ) + '&create=y';
                        send_data += '&share_password=' + $('input[name=share_password]').val();
                        send_data += '&share_password_confirm=' + $('input[name=share_password_confirm]').val();
                        send_data += '&share_expire_time=' + $('select[name=share_expire_time]').val();
                        
                        $.ajax({
                                type:"POST",
                                url:FileOperations.urls.share_file,
                                data: send_data,
                                beforeSend : function(xhr, options) {
                                    FileOperations.is_working = true;
                                },
                                success : function(data, status, xhr) {
                                    dlg.dialog('option', 'buttons',[
                                        {
                                            text : Skylable_Lang['closeBtn'],
                                            click : function(e) {
                                                dlg.dialog('close');
                                                dlg.dialog('destroy');
                                            }
                                        }
                                    ]);
                                    dlg.html(xhr.responseText);
                                    $('#shared_file_url_input').select().focus();

                                },
                                error : function(xhr, status) {
                                    if (!FileOperations.expiredUser(dlg, xhr)) {
                                        dlg.html(xhr.responseText);
                                    }
                                },
                                complete : function(xhr, status) {
                                    FileOperations.is_working = false;
                                }
                        });
                        
                    }
                },
                    {
                        text: Skylable_Lang['noBtn'],
                        click: function(e) {
                            dlg.dialog('close');
                            dlg.dialog('destroy');
                        }
                    }
            ]);

            $.ajax({
                type:"POST",
                url:FileOperations.urls.share_file,
                data:'path='+encodeURIComponent( path ),
                beforeSend : function(xhr, options) {
                    FileOperations.is_working = true;
                },
                success : function(data, status, xhr) {
                    dlg.html(xhr.responseText);
                    // dlg.dialog('open');
                },
                error : function(xhr, status) {
                    
                    if (!FileOperations.expiredUser(dlg, xhr)) {
                        dlg.html(xhr.responseText);
                        dlg.dialog('option', 'buttons',[{
                            text : Skylable_Lang['closeBtn'],
                            click : function(e) {
                                dlg.dialog('close');
                                dlg.dialog('destroy');
                            }
                        }]);
                    }
                },
                complete : function(xhr, status) {
                    FileOperations.is_working = false;
                    dlg.dialog('open');
                }
            });
           
        },

        /**
         * Close and remove the preview lightbox
         * @param e
         */
        removePreview : function(e) {
            $(document).off("keydown.preview");
            $(window).off("resize.preview");
            $('#preview-overlay, #preview-lightbox, #preview-nav-bar')
                .fadeOut('slow', function(){
                    $(this).remove();
                });
        },
        preview_current: null,
        preview_next: null,
        preview_prev: null,
        preview_index: 0,

        /**
         * Find the next and previous files to preview.
         *
         * If file_url is not null starts showing from that file,
         * else use the FileOperation.preview_index to do calculations.
         *
         * @param file_url
         */
        previewFindNextPrevElement : function(file_url) {
            var elements = $('.elmpreview');

            // Starts from this index
            if (file_url) {
                file_url = Skylable_Utils.basename(file_url);
                for(var idx = 0; idx < elements.length; idx++) {
                    var href = Skylable_Utils.basename( $(elements.get(idx)).attr('href') );
                    if (href === file_url) {
                        FileOperations.preview_index = idx;
                        break;
                    }
                }
            }

            if (FileOperations.preview_index == 0) {
                // FileOperations.preview_prev = elements.get( elements.length - 1 );
                FileOperations.preview_prev = null;
            } else {
                FileOperations.preview_prev = elements.get( FileOperations.preview_index - 1 );
            }

            if (FileOperations.preview_index == elements.length - 1) {
                // FileOperations.preview_next = elements.get(0);
                FileOperations.preview_next = null;
            } else {
                FileOperations.preview_next = elements.get( FileOperations.preview_index + 1 );
            }

            FileOperations.preview_current = elements.get( FileOperations.preview_index );

        },

        /**
         * Setup the preview navbar actions
         *
         * @param file_url
         */
        previewFileSetupNavbar : function(file_url) {
            $('#preview-nav-bar-close').click(function(e){
                FileOperations.removePreview();
                e.preventDefault();
            });
            $('#preview-nav-bar-download').click(function(e){
                window.open( $(FileOperations.preview_current).attr('href') );
                e.preventDefault();
            });
            FileOperations.previewFindNextPrevElement(file_url);
            var elements = $('.elmpreview');

            $('#preview-nav-bar-next').click(function(e){
                if (FileOperations.preview_next !== null) {
                    FileOperations.previewShowFile($(FileOperations.preview_next).attr('href'), $(FileOperations.preview_next).data('filetype') );
                    // Advance the preview index
                    FileOperations.preview_index++;
                    if (FileOperations.preview_index >= elements.length) {
                        FileOperations.preview_index = elements.length - 1;
                    }
                }

                FileOperations.previewFindNextPrevElement();
                e.preventDefault();
            });

            $('#preview-nav-bar-prev').click(function(e){
                if (FileOperations.preview_prev !== null) {
                    FileOperations.previewShowFile($(FileOperations.preview_prev).attr('href'), $(FileOperations.preview_prev).data('filetype'));
                    // Advance the preview index
                    FileOperations.preview_index--;
                    if (FileOperations.preview_index < 0) {
                        FileOperations.preview_index = 0;
                    }
                }
                FileOperations.previewFindNextPrevElement();
                e.preventDefault();
            });

        },

        /**
         * Preview a file into the browser window
         *
         * @param file_url the complete URL to show
         * @param file_type the file type
         */
        previewFile : function(file_url, file_type) {
            // $('body').css('overflow-y', 'hidden');


            $('<div id="preview-overlay"></div>')
                .css('opacity', '0')
                .animate({'opacity': '0.5'}, 'slow')
                .click(FileOperations.removePreview)
                .appendTo('body');
            $('<div id="preview-lightbox"></div>')
                .hide()
                .appendTo('body');

            $('<div id="preview-nav-bar">' +
                '<span class="preview-nav-bar-text" id="preview-nav-bar-filename"></span>' +
                '<a class="preview-nav-bar-btn" id="preview-nav-bar-close">' + Skylable_Lang['previewCloseBtn'] + '</a>' +
                '<a class="preview-nav-bar-btn" id="preview-nav-bar-download">' + Skylable_Lang['previewDownloadBtn'] + '</a>' +
                '<a class="preview-nav-bar-btn" id="preview-nav-bar-prev">' + Skylable_Lang['previewPrevBtn'] + '</a>' +
                '<a class="preview-nav-bar-btn" id="preview-nav-bar-next">' + Skylable_Lang['previewNextBtn'] + '</a>' +
            '</div>')
                .hide()
                .appendTo('body');

            FileOperations.previewFileSetupNavbar(file_url);
            FileOperations.previewShowFile(file_url, file_type);

            // Bind the ESC key to close the window
            $(document).on("keydown.preview", function(event){
                if (event.which == 27) {

                    FileOperations.removePreview(event);

                    // $(document).off('keydown.preview', this);
                }
            });

            $(window).on("resize.preview", function(event){
                var pnb = $('#preview-nav-bar');
                var lb = $('#preview-lightbox');
                $(lb).css({
                    'top' : 20 + $(pnb).height(),
                    'width' : $(window).width() - 40,
                    'height': $(window).height() - 60
                }).css({
                    // 'top': 40 + (($(window).height() - $(lb).height()) / 2),
                    'left': (($(window).width() - $(lb).width()) / 2)
                })
            });
        },

        /**
         * Do the effective file preview, need that everything is already set up
         * by FileOperations.previewFile
         * @param file_url the file to show
         * @param file_type the file type
         */
        previewShowFile : function(file_url, file_type) {

            // Update the current showed file name
            $('#preview-nav-bar-filename')
                .html( Skylable_Utils.trim_str_center( Skylable_Utils.basename(file_url), 30 ) )
                .attr('title', Skylable_Utils.basename(file_url) );

            var pnb = $('#preview-nav-bar');
            $(pnb)
                .css({
                    'top' : 0,
                    'width': '100%',
                    'margin' : '0 auto',
                    'padding' : '4px 0',
                    'text-align' : 'center'
                });

            var lb = $('#preview-lightbox');
            $(lb).empty()
                .css({
                'top' : 20 + $(pnb).height(),
                'width' : $(window).width() - 40,
                'height': $(window).height() - 60,
                'background' : 'transparent',
                'overflow' : 'hidden'
            }).css({
                'left': (($(window).width() - $(lb).width()) / 2)
            });

            $('#preview-overlay').css('background-image','');

            if (file_type === 'pdf') {
                $('<iframe id="preview-pdf"></iframe>')
                    .attr('src', '/.sxshare/static/pdfjs/web/viewer.html?file=' + window.location.pathname + encodeURIComponent(file_url + '?download') + '&_c=' + Math.random())
                    .css('width', '100%')
                    .appendTo(lb);

                $('#preview-pdf').css('height', '100%' );

                $(lb).fadeIn();
                $(pnb).fadeIn();

            } else if(file_type === 'source' || file_type === 'text') {

                $.ajax({
                    url : file_url,
                    cache : false,
                    success: function(data, status, xhr) {
                        // $('#preview-overlay').css('background-image','none');

                        $.getScript('/.sxshare/static/js/run_prettify.js');

                        $('<pre class="prettyprint" id="preview-source"></pre>')
                            .css('width','100%')
                            .css('background', '#fff')
                            .appendTo('#preview-lightbox');

                        $('#preview-source').html( data.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') );

                        $(lb).css({
                            'background': '#fff',
                            'overflow' : 'auto',
                            'text-align' : 'left',
                            'vertical-align' : 'top'
                        }).fadeIn();

                        $(pnb).fadeIn();
                    },
                    error : function (xhr, status) {
                        var dlg = FileOperations.getDialog(Skylable_Lang['previewErrorTitle']);
                        dlg.html('<p>'+Skylable_Lang['previewLoadFailed']+'</p>');
                        dlg.dialog('option', 'buttons', [{
                            text: Skylable_Lang['closeBtn'],
                            click:function(e) {
                                dlg.dialog('close');
                            }
                        }]);
                        dlg.dialog('open');
                    }
                });
            } else {
                $('<img />')
                    .on('error', function(ev){
                        var dlg = FileOperations.getDialog(Skylable_Lang['previewErrorTitle']);
                        dlg.html('<p>'+Skylable_Lang['previewLoadFailed']+'</p>');
                        dlg.dialog('option', 'buttons', [{
                            text: Skylable_Lang['closeBtn'],
                            click:function(e) {
                                dlg.dialog('close');
                            }
                        }]);
                        dlg.dialog('open');
                    })
                    .on('load',function(ev){
                        $('#preview-overlay').css('background-image','none');
                        $(lb).css({
                            'text-align' : 'center'
                        }).fadeIn();

                        $(pnb).fadeIn();
                    })
                    .click(FileOperations.removePreview)
                    .attr('src', file_url + '?_c=' + Math.random())
                    .css({ 'max-width' : '100%', 'max-height' : '100%', 'vertical-align' : 'middle' })
                    .appendTo(lb);
            }
        },

        /**
         * Assigns event handlers on the entire page
         */
        assignHandlers : function() {
            $('a#createdir').click(this.createDir);
            $('a#actioncopy').click(this.copy);
            $('a#actionmove').click(this.move);
            $('a#actiondelete').click(this.deleteFiles);
            this.assignFileListHandlers();
        },

        /**
         * Get the base dialog.
         *
         * @param title dialog title
         * @returns {*|jQuery|HTMLElement}
         */
        getDialog : function(title) {
            var dlg = $('#dialog');
             
            dlg.dialog({
                autoOpen: false,
                modal: true,
                resizable: true,
                title: title,
                width: Skylable_Utils.defaultDialogWidth(),
                beforeClose: function(ev, ui) {
                    // Avoids closing while AJAX calls
                    if (FileOperations.is_working) {
                        return false;
                    }
                }
            });
            return dlg;
        }

    }
}

$(document).ready(function(){
    FileOperations.assignHandlers();
});
