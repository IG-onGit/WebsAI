$(document).ready(function () {
  // Click-to-copy for .cmd-copy
  $(".cmd-copy").on("click", function () {
    let $btn = $(this),
      cmd = $btn.data("cmd");
    if (!cmd) return;

    function onCopied(success) {
      $(".cmd-copy").removeClass("copied");
      if (success) {
        $btn.addClass("copied");
        App.success("Copied: " + cmd);
        setTimeout(() => {
          $btn.removeClass("copied");
        }, 1100);
      } else {
        App.error("Failed to copy.");
      }
    }

    // Try Native clipboard API
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      navigator.clipboard.writeText(cmd).then(
        function () {
          onCopied(true);
        },
        function () {
          onCopied(false);
        }
      );
      return;
    }

    // Fallback method via execCommand
    try {
      let $temp = $("<textarea readonly></textarea>");
      $temp.val(cmd).css({
        position: "absolute",
        left: "-9999px",
        top: (window.pageYOffset || document.documentElement.scrollTop) + "px",
      });
      $("body").append($temp);
      $temp[0].focus();
      $temp[0].select();
      let success = false;
      try {
        success = document.execCommand("copy");
      } catch (e) {
        success = false;
      }
      $temp.remove();
      onCopied(success);
    } catch (e) {
      onCopied(false);
    }
  });
});
