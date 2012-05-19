	google.load("search", "1");
	var searchControl;

    function OnLoad() {
		searchControl = new google.search.SearchControl();
		searchControl.setResultSetSize(google.search.Search.SMALL_RESULTSET);
		searchControl.setLinkTarget(google.search.Search.LINK_TARGET_SELF);

		var webSearch = new google.search.WebSearch()
		var imageSearch = new google.search.ImageSearch()

		webSearch.setSiteRestriction('douban.com');
		imageSearch.setSiteRestriction('douban.com');

		searchControl.addSearcher(webSearch);
		searchControl.addSearcher(imageSearch);

		var drawOptions = new google.search.DrawOptions();
		drawOptions.setDrawMode(google.search.SearchControl.DRAW_MODE_TABBED);

		searchControl.draw(document.getElementById("searchcontrol"), drawOptions);

        document.getElementsByName("search")[0].onkeyup = new Function("localSearch(this.value);");     
        document.getElementsByName("search")[0].onclick = new Function("this.value = '';this.style.color = 'black'");    
        document.getElementsByName("search")[0].value = "Suchen...";     
		document.getElementsByName("search")[0].style.color = '#ccc';
		getElementByClass('gsc-search-button')[0].onclick = new Function("localSearch(document.getElementsByName('search')[0].value);");
		getElementByClass('gsc-search-box')[0].onsubmit = new Function("alert('hier');return false;");
		getElementByClass('gsc-search-button')[0].style.display = 'none';
		getElementByClass('gsc-clear-button')[0].style.display = 'none';
    }

    google.setOnLoadCallback(OnLoad);

	function localSearch(keyword){
		searchControl.execute(keyword);
		document.getElementById("searchcontrol").style.height = 'auto';
		document.getElementById('searchcontrol').style.backgroundColor = '#fff';
		document.getElementById('searchcontrol').style.border = '1px solid black';
	}

	function getElementByClass(theClass) {
		var allHTMLTags = new Array();
		var res = new Array();
		var allHTMLTags=document.getElementsByTagName("*");
		for (i=0; i<allHTMLTags.length; i++) {
			if (allHTMLTags[i].className==theClass) {
				res[res.length] =  allHTMLTags[i];
			}
		}
		return res;
	}