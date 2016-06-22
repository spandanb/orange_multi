/* A hack to extract the GCE instances prices.
* Steps: 
* 1) Goto: https://cloud.google.com/compute/pricing
* 2) Copy and paste this code in the console; it will output some JSON
*        that you can pasted in a .json file
* NOTE: if the HTML structure of the page changes; this won't work
*/

var getprices = function(table){
    //returns a list of maps from field to value
    //each table consists of multiple members of machine types in a family
    //each map maps the labels to their values

    //column labels (machine type, vcpu, memory, gce units, lowest price, typical price, full price, pre-emptible price)
    var labels = ["mtype", "vcpu", "memory", "gceu", "lowest", "typical", "full", "prempt" ]

    results = []; //scraped data
    rows = table.getElementsByTagName("tr")
    for(var i=1; i<rows.length; i++){
        var cols = rows[i].getElementsByTagName("td")
        if(cols.length == labels.length){ //this avoid adding bogus rows
            var map = {}
            for(var j=0; j<cols.length; j++)
                map[labels[j]] = cols[j].innerText
            results.push(map)
        }
    }
    return results
}

var gettables = function(){
    //Prints a JSON object mapping table name (family) to list of machine types in that family

    //get all the tables
    var tables = document.getElementsByClassName("devsite-table-wrapper");
    //The table for stdprices
    var tablenames = []
    tablenames[0] = "std" //us
    tablenames[4] = "std-eu"
    tablenames[5] = "micro-bursting"
    tablenames[6] = "high-mem"
    tablenames[7] = "high-cpu"
    var output = {}
    for(var i=0; i<tablenames.length; i++){
        console.log(tables[i])
        if(!!tablenames[i]) output[tablenames[i]] = getprices(tables[i])
    }
    console.log(JSON.stringify(output));
}
gettables()
