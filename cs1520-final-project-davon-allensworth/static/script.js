const months = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]

var d = new Date();
var month = document.createElement('h3');
var monthDiv = document.getElementById("currMonth");
month.innerText = "Budget for month of: " + months[d.getMonth()];
monthDiv.appendChild(month);

categories = [];
purchases = [];

function refreshData(){
    /*
    Promise.all([
        getCategories(),
        getPurchases(),
    ]).then(updateBudget)
    */
    getCategories();
    getPurchases();
}

function updateBudget(){
    listCategories();
}

function getCategories(){
    var request = new XMLHttpRequest();
    request.onreadystatechange = function() { getCategoriesSuccess(request) };
    request.open("GET", "/cats");
    request.send();
}

function getPurchases(){
    var request = new XMLHttpRequest();
    request.onreadystatechange = function() { getPurchasesSuccess(request) };
    request.open("GET", "/purchases");
    request.send();
}

function getCategoriesSuccess(request){
    if (request.readyState === XMLHttpRequest.DONE) {
        if (request.status === 200) {
            console.log("Categories:  " + request.responseText);
            var response = request.responseText;
            categories = JSON.parse(response);
        }
        else{
            alert("There was an error retrieving categories.");
        }
    }
}

function getPurchasesSuccess(request){
    if (request.readyState === XMLHttpRequest.DONE) {
        if (request.status === 200) {
            console.log("Purchases:  " + request.responseText);
            var response = request.responseText;
            purchases = JSON.parse(response);
        }
        else{
            alert("There was an error retrieving purchases.");
        }
    }
}

function calculateStatus(category, limit){
    var cat_purchases = purchases.filter(purchase => purchase.category === category);

    total = 0;
    for (var i=0; i < cat_purchases.length; i++){
        total += parseFloat(cat_purchases[i].amount);
    }
    if(total >= limit)
       return "overspent";
    else
        return "$" + total;
}

function listCategories(responseData){
    var table = document.getElementById("categories");

    while (table.rows.length > 1) {
    		table.deleteRow(1);
    	}

    for(var i = 0; i < categories.length; i++){
        var name = categories[i].name;
        var limit = categories[i].limit;
        var newRow = table.insertRow();
        nameCell = newRow.insertCell();
        nameCell.innerHTML = name;

        statusCell = newRow.insertCell();
        var status = calculateStatus(name, limit);
        statusCell.innerHTML = status;

        limitCell = newRow.insertCell();
        limitCell.innerHTML = "$" + limit;
        deleteCell = newRow.insertCell();
        deleteCell.innerHTML = "Delete";
        deleteCell.addEventListener("click", function(){deleteCategory(name)});
    }
    var lastRow = table.insertRow();
    nameCell = lastRow.insertCell();
    nameCell.innerHTML = "Uncategorized";
    statusCell = lastRow.insertCell();
    var status = calculateStatus("", "10000000000000");
    statusCell.innerHTML = status;

}

function addCategory(){
    do{
        var name = prompt("Enter the name of the category: ");
        if(name == null){
            return;
        }
    }
    while(name == "");
    do{
        var limit = prompt("Enter the price limit for this category: $");
        if(limit == null){
            return;
        }
    }
    while(limit == "" && isNaN(limit));

    data = "name=" + name + "&limit=" + parseFloat(limit);
    generateRequest("POST", "/cats", 200, refreshData, data);
    alert('Category was added. Update by clicking "Get Info"');
}

function addPurchase(){
    var description = document.getElementById("description").value
    var amount = document.getElementById("amount").value
    var date = document.getElementById("date").value
    var category = document.getElementById("category").value

    var data = "description=" + description + "&amount=" + amount + "&date=" + date + "&category=" + category;
    generateRequest("POST", "/purchases", 200, refreshData, data);

    document.getElementById("description").value = "";
    document.getElementById("amount").value = "";
    document.getElementById("date").value = "";
    document.getElementById("category").value = "";
}

function deleteCategory(categoryId){
    if (confirm('Are you sure you want to delete the category: ' + categoryId + ' ?')) {
      generateRequest("DELETE", "/cats/" + categoryId, 204, refreshData);
      alert('Category was deleted. Update by clicking "Update Info"');
    } else {
      alert('Category was not deleted.');
    }
}


// HTTP Request Generation
function generateRequest(method, targetURL, returnCode, handlerAction, data){
    var request = new XMLHttpRequest();

    request.onreadystatechange = setHandler(request, returnCode, handlerAction);
    request.open(method, targetURL);

    //if user passes in data, encode for safety.
    if (data) {
    	request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    	request.send(data);
    }
    else {
    	request.send();
    }
}

// Request Status Handling
// Layout inspired by "fl13_restful" for speed.
function setHandler(request, returnCode, action) {
    function handler() {
		if (request.readyState === XMLHttpRequest.DONE) {
			if (request.status === returnCode) {
				console.log("Response text:  " + request.responseText);
				//perform the specified action w returned data
				action(request.responseText);
			} else {
				alert("Error performing request. Please refresh the page.");
			}
		}
	}
	return handler;
}

// initial load event
window.addEventListener("load", refreshData, true);
document.getElementById("addPurchase").addEventListener("click", addPurchase, true);