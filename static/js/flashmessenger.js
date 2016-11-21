// Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
// License: MIT, see LICENSE for more details.

// Enable dismiss on flashMessenger messages
$(function() {
	$(".icon-failure, .icon-success").click(function() {
		$(this).parent().parent().remove();
	});	
});

