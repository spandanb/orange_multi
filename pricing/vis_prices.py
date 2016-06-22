"""
Visualizes GCE and AWS spot prices. 
There are two methods, that provide a 3-d and 2-d visualization, resp.
"""
import json, pdb, re
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import numpy as np

def get_gce_data(fpath="gce_prices.json", mtype=None, price='typical'):
    """
    Reads the data file and returns scrubbed and formatted data
    Arguments:
        fpath:- path to data file
        mtype:- the type of machine, defaults to all {std, std-eu, micro-bursting, high-mem, high-cpu}
    Returns x,y,z array
        price:- the price to use, {typical, full, lowest}

    """

    with open(fpath) as fptr:
        data = json.load(fptr)

    if not mtype:
        #NOTE: ALL types excludes std-eu
        mtypes = ["std", "micro-bursting", "high-mem", "high-cpu"]
        
        prices = np.array([float(m[price][1:]) for mtype in mtypes for m in data[mtype]])
        cpu = np.array([float(m['vcpu']) for mtype in mtypes for m in data[mtype]])
        mem = np.array([float(m['memory'][:-2]) for mtype in mtypes for m in data[mtype]])
            
    else:
        machines = data[mtype]
        prices = np.array([float(m[price][1:]) for m in machines])
        cpu = np.array([float(m['vcpu']) for m in machines])
        mem = np.array([float(m['memory'][:-2]) for m in machines])

    return {"cpu": cpu, "mem":mem, "prices":prices}   

def get_aws_data(fpath="aws_prices.jsonp", region="us-east-1"):
    """
    """
    with open(fpath) as fptr:
        jsonp = fptr.read()
        #convert jsonp to json
        data = jsonp[ jsonp.index("(") + 1 : jsonp.rindex(")") ]
        #quote the key in the jsonp data
        quote_keys_regex = r'([\{\s,])(\w+)(:)'
        data = re.sub(quote_keys_regex, r'\1"\2"\3', data)
        data = json.loads(data)

    families = next(rgn['instanceTypes'] for rgn in data['config']['regions'] if rgn['region'] == region) 
    #families e {generalCurrentGen, computeCurrentGen, gpuCurrentGen, hiMemCurrentGen, storageCurrentGen}
    
    #Do all families
    prices = np.array([float(flavor['valueColumns'][0]['prices']['USD']) for fam in families for flavor in fam["sizes"]])
    mem    = np.array([float(flavor['memoryGiB']) for fam in families for flavor in fam["sizes"]])
    cpu    = np.array([float(flavor['vCPU']) for fam in families for flavor in fam["sizes"]])

    return {"cpu": cpu, "mem":mem, "prices":prices}   
        

def _visualize_3d(x, y, z, ax, marker='o', color='b', label=None):
    """
    x,y,z don't form a smooth function. Therefore, the surface plot 
    must approximate a smooth surface based on some data points, and with
    only a small number of points the surface is very irregular. 
    """
    
    #surface plot 1
    #See: http://stackoverflow.com/questions/21161884/plotting-a-3d-surface-from-a-list-of-tuples-in-matplotlib?lq=1
    #grid_x, grid_y = np.mgrid[min(x):max(x):100j, min(y):max(y):100j]
    #grid_z = griddata((x, y), z, (grid_x, grid_y), method='cubic')
    #ax.plot_surface(grid_x, grid_y, grid_z, cmap=plt.cm.Spectral)

    #surface plot 2
    #http://stackoverflow.com/questions/12423601/python-the-simplest-way-to-plot-3d-surface
    #surf = ax.plot_trisurf(x, y, z, cmap=cm.jet, linewidth=0)
    
    plt.hold(True) #needed to combine both plot

    #plot scatter
    ax.plot(x, y, z, marker, color=color, label=label) 

def visualize_3d():
    """
    Plots the surface plot and scatter plot of price = f(vCPUs, memory) for
    GCE and AWS.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    #GCE
    data = get_gce_data()
    _visualize_3d(data["cpu"], data["mem"], data["prices"], ax, marker='o', color='b', label='gce')
    #AWS
    data = get_aws_data()
    _visualize_3d(data["cpu"], data["mem"], data["prices"], ax, marker='^', color='r', label='aws')
    
    plt.legend(loc='upper left', numpoints=1, ncol=3, fontsize=8, bbox_to_anchor=(0, 0))

    ax.set_xlabel('vCPU')
    ax.set_ylabel('Memory (GB)')
    ax.set_zlabel('Prices ($/hr)')

    plt.show()

def _visualize2d(gce, aws, xaxis=None):
    """
    Plots scatter plot and line of bestfit

    Arguments:
        gce, aws: dicts of lists to plot, i.e. {'x':[], 'y':[]}
        xaxis: name of xaxis
    """
    def scatter_plot(x, y, ax, marker='o', color='b'):
        return ax.scatter(x, y, color=color, marker=marker, alpha=0.5)
    
    mgce, bgce = np.polyfit(gce['x'], gce['y'], 1)
    maws, baws = np.polyfit(aws['x'], aws['y'], 1)

    fig, ax = plt.subplots()
    glabel = scatter_plot(gce['x'], gce['y'], ax, marker='o', color="b")
    alabel = scatter_plot(aws['x'], aws['y'], ax, marker='^', color="r")
    
    #plot line of best fit
    plt.plot(gce['x'], mgce*gce['x'] + bgce, '-')
    plt.plot(aws['x'], maws*aws['x'] + baws, '-')

    plt.legend((glabel, alabel), ('GCE', 'AWS'), scatterpoints=1, loc='lower left', fontsize=8)
    ax.grid(True)
    ax.set_xlabel(xaxis, fontsize=20)
    ax.set_ylabel('price', fontsize=20)
    ax.set_title('Price vs. {}'.format(xaxis))

def visualize_2d():
    gce = get_gce_data(price="full")
    aws = get_aws_data()

    #visualize memory
    _visualize2d({'x':gce['mem'], 'y': gce['prices']}, {'x':aws['mem'], 'y': aws['prices']}, xaxis="mem")
    
    #visualize CPU
    _visualize2d({'x':gce['cpu'], 'y': gce['prices']}, {'x':aws['cpu'], 'y': aws['prices']}, xaxis="cpu")
    
    #visualize CPU * Memory
    gcep = gce['cpu'] * gce['mem']
    awsp = aws['cpu'] * aws['mem'] 
    _visualize2d({'x':gcep, 'y': gce['prices']}, {'x':awsp, 'y': aws['prices']}, xaxis="cpu * mem")

    plt.show()

if __name__ == "__main__":
    visualize_3d()
    visualize_2d()
