# Tweet Analyzing Server

This server receives an input from the user in the form of a list of tokens separated by spaces. It processes this list within its database of tweets and returns some interesting visualizations based on its results.

## Getting Started

These instructions will get your copy of the tweet analyzing server up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them:

```
Docker Desktop with Kubernetes
```

### Installing

A step-by-step series of examples that tell you how to get a development environment running.

#### 1. Clone the project

Start by cloning the project to your local machine:

```bash
git clone https://github.com/Xilandia/Tweet-Analyzer-Final-Project.git
cd Tweet-Analyzer-Final-Project
```

#### 2. Build each image

Navigate to each service directory and build the Docker images. Replace `service_name` with the actual service names:

```bash
cd path/to/service
docker build -t service_name:latest .
```

Repeat this step for each of the microservices.

#### 3. Apply the Kubernetes configurations

Navigate to the `kubernetes` folder and apply the configurations:

```bash
cd path/to/kubernetes
kubectl apply -f .
```

This will set up all necessary Kubernetes resources, such as Deployments, Services, and any other configurations you have defined.

#### 4. Expose the Ingress

Because we ran using a local environment, we had to manually expose the Ingress via port forwarding:

```bash
kubectl port-forward service/nginx-ingress-ingress-nginx-controller 8080:80 -n default
```

This will set up the server, and it will start running on its own once it has sufficient resources.



## Built With

* [NodeJS](https://nodejs.org/en) - The web framework used for the web-interface-service and input-parsing-service
* [Flask](https://flask.palletsprojects.com/en/3.0.x/) - The Python app framework used for the rest of the services

## Contributing

Please shoot me a message at omer_segal@live.com if you have any questions or want to continue this project.

## Authors

* **Omer Segal** - *Initial work* - [Xilandia](https://github.com/Xilandia)
* **Fanny Guthmann** - *Initial work* - [fguthmann](https://github.com/fguthmann)