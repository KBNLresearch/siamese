var ANNOY_RANDOM = "../annoy/random";
var ANNOY_QUERY = "../annoy/query";

$(function() {

    function annoy(url, callback, params) {
        $.ajax({
            type: "GET",
            url: url,
            data: params,
            success: function(data) {
                console.log(data);
                callback(data);
            }
        });
    }

    function search_random_urn(data) {
        var urn = data["images"][0]["urn"];
        search_urn(urn);
    }

    function search_urn(urn) {
        var neighbors = annoy(ANNOY_QUERY, show_neighbors, "urn=" + urn);
    }

    function show_neighbors(data) {
        var urn = data["source"]["urn"];
        if ($("input#urn").val().search(urn) == -1) {
            $("input#urn").val(urn);
        }
        show_source(data["source"]);
        for (var step in data["neighbors"]) {
            show_thumb_list(data["neighbors"][step], step);
        }
    }

    function show_random_images(data) {
        show_thumb_list(data, 'random');
    }

    function show_source(data) {
        var path = "images/" + data["year"] + "/" + data["image"];
        var html = '<img class="source" src="' + path + '">';
        $("#source").html(html);
    }

    function show_thumb_list(data, step) {
        var html = "";
        for (var start_year in data) {
            for (var neighbor in data[start_year]) {
                html += get_thumb_html(
                    data[start_year][neighbor]["path"],
                    data[start_year][neighbor]["year"],
                    data[start_year][neighbor]["urn"]
                );
            }
        }
        $("#" + step).html(html);
    }

    function get_thumb_html(path, year, urn) {
        var html = "";

        // Container div
        html += '<div class="thumb-container">';

        // Image thumbnail
        html += '<a href="?urn=' + urn + '">';
        html += '<img class="thumb" src="thumbs/' + path + '">';
        html += '</a>';

        // Year
        var url = 'http://resolver.kb.nl/resolve?urn=' + urn;
        html += '<div class="year">';
        html += ' <a href="' + url + '" target="_blank">' + year + '</a>';
        html += "</div>";

        html += "</div>";

        return html;
    }

    var url = window.location.href;

    if (url.split("urn=").length == 2) {
        
        urn = url.split("urn=")[1];
        urn = decodeURIComponent(decodeURIComponent(urn));

        if (urn.split("resultsidentifier=").length == 2) {
            urn = urn.split("resultsidentifier=")[1]
        } else if (urn.split("urn=").length == 2) {
            urn = urn.split("urn=")[1]
        }

        if (history.pushState) {
            var new_url = window.location.protocol + "//";
            new_url += window.location.host;
            new_url += window.location.pathname;
            new_url += '?urn=' + urn;
            window.history.pushState({path: new_url}, '', new_url);
        }

        search_urn(urn);

    } else {
        annoy(ANNOY_RANDOM, search_random_urn, null);
    }

    annoy(ANNOY_RANDOM, show_random_images, null);

});

