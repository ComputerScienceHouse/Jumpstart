var lastRefresh = new Date(); // If the user just loaded the page you don't want to refresh either
var counter = 1;
setInterval(function(){
  //first, check time, if it is 9 AM, reload the page
  var now = new Date();
         
  if (counter == 0 && (now.getMinutes() == 1 || now.getMinutes() == 30)) { // If it is between 9 and ten AND the last refresh was longer ago than 6 hours refresh the page.
    counter++;
    location.reload();
  }
  if(!(now.getMinutes() == 1) && !(now.getMinutes() == 30)){
    counter = 0;
  }
//do other stuff
}, 1000);