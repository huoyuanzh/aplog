replyComment={
	I : function(a) {
		return document.getElementById(a)
	},
	showForm:function(commentNode,commentid,f,post_id){
		var k = this, a, g = k.I(commentNode), b = k.I(f), j = k.I("cancel-comment-reply");
		
		if (!g || !b || !j) {
			return
		}
		k.respondId = f;
		k.I(f).style.display="block";
		k.I('post_id').value=post_id;
		k.I('parent_id').value=commentid;
		if (!k.I("wp-temp-form-div")) {
			a = document.createElement("div");
			a.id = "wp-temp-form-div";
			a.style.display = "none";
			b.parentNode.insertBefore(a, b)
		}
		g.parentNode.insertBefore(b, g.nextSibling);
		
		j.onclick = function() {
			var l = replyComment, e = l.I("wp-temp-form-div"), m = l.I(l.respondId);
			if (!e || !m) {
				return
			}
			e.parentNode.insertBefore(m, e);
			e.parentNode.removeChild(e);
			m.style.display="none";
			this.onclick = null;
			return false
		};
	}
}