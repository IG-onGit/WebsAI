var App = {
  //X> Main
  /**
   * Display success message
   * @param {string} message - Alert message
   */
  error: function (message) {
    this._showToast(message, "error");
  },

  /**
   * Display info message
   * @param {string} message - Alert message
   */
  info: function (message) {
    this._showToast(message, "info");
  },

  /**
   * Display success message
   * @param {string} message - Alert message
   */
  success: function (message) {
    this._showToast(message, "success");
  },

  /**
   * Call PHP backend methods via AJAX
   * @param {string} page - PHP class file name (without .php)
   * @param {string} method - Public method name in PHP class
   * @param {object} data - Data to send
   * @param {function} code - Callback function to handle response
   */
  call: function (page, method, data, code) {
    $.ajax({
      url: page.toLowerCase(),
      type: "POST",
      data: { "websai-call": method, ...data },
      success: function (response) {
        if (typeof code === "function") {
          code(response);
        }
      },
      error: function (xhr, status, err) {
        App.error("Call Error: " + err);
      },
    });
  },

  loaded: function loaded() {
    setTimeout(() => {
      $("#websai-loader").fadeOut("slow");
    }, 500);
    setTimeout(() => {
      $("#websai-loader").remove();
    }, 1500);
  },

  //X> Helpers
  _initToastContainer: function () {
    if ($("#app-toast-container").length === 0) {
      $("body").append('<div id="app-toast-container" style="position: fixed; bottom: 20px; right: 20px; z-index: 9999;"></div>');
    }
  },

  _showToast: function (message, type) {
    this._initToastContainer();

    var colors = {
      error: "rgb(252, 70, 70)",
      info: "rgb(51, 179, 218)",
      success: "rgb(51, 218, 58)",
    };
    var icons = {
      error: "fa-circle-xmark",
      info: "fa-circle-question",
      success: "fa-circle-check",
    };

    var borderColor = colors[type] || "#333";
    var iconClass = icons[type] || "fa-circle-info";

    var toast = $("<div></div>")
      .css({
        background: "#202020",
        border: "1px solid " + borderColor,
        padding: "12px 15px 12px 10px",
        marginTop: "10px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        borderRadius: "8px",
        minWidth: "250px",
        fontFamily: "Arial, sans-serif",
        color: borderColor,
        opacity: 0,
        cursor: "pointer",
        position: "relative",
        right: "-20px",
        display: "flex",
        alignItems: "center",
        fontWeight: "normal",
        gap: "10px",
      })
      .append($("<i></i>").addClass(`fa-regular ${iconClass}`).css({ "font-size": "24px", "font-weight": "normal" }), $("<span></span>").text(message))
      .appendTo("#app-toast-container")
      .animate({ opacity: 1, right: "0px" }, 300);

    setTimeout(() => {
      toast.animate({ opacity: 0, right: "-20px" }, 300, function () {
        $(this).remove();
      });
    }, 3000);

    toast.on("click", function () {
      $(this).remove();
    });
  },
};
