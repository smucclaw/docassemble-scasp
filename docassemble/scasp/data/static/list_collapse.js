$(document).on('daPageLoad', function(){
var toggler = document.getElementsByClassName("caret");
var toggler_count;

for (toggler_count = 0; toggler_count < toggler.length; toggler_count++) {
(function(x){
    toggler[x].addEventListener("click", function() {
      toggler[x].parentElement.querySelector(".nested").classList.toggle("active");
      toggler[x].classList.toggle("caret-down");
    });
  })(toggler_count)
}
});