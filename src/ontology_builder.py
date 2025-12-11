"""
RDF/OWL Ontology Module
Builds a knowledge graph and queries it with SPARQL

Python builds the .ttl file, then we use SPARQL for actual queries.

CPSC 583 Project
Authors: Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia
"""

from rdflib import Graph, Namespace, Literal, RDF, RDFS, OWL, URIRef
from rdflib.namespace import XSD
import pandas as pd
from pathlib import Path


class CarOntology:
    """
    RDF/OWL ontology for car data.

    We build the graph from the dataframe, save it to .ttl,
    then use SPARQL queries for reasoning at runtime.
    """

    def __init__(self):
        self.graph = Graph()

        # our custom namespace
        self.CAR = Namespace("http://example.org/cars#")
        self.graph.bind("car", self.CAR)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdfs", RDFS)

        self._define_schema()

    def _define_schema(self):
        # Define the ontology schema 

        # Classes
        self.graph.add((self.CAR.Vehicle, RDF.type, OWL.Class))
        self.graph.add((self.CAR.Manufacturer, RDF.type, OWL.Class))

        # Subclasses for body types
        for body_type in ['Sedan', 'SUV', 'Truck', 'Coupe', 'Hatchback', 'Wagon']:
            uri = self.CAR[body_type]
            self.graph.add((uri, RDF.type, OWL.Class))
            self.graph.add((uri, RDFS.subClassOf, self.CAR.Vehicle))

        # Object properties
        self.graph.add((self.CAR.madeBy, RDF.type, OWL.ObjectProperty))
        self.graph.add((self.CAR.madeBy, RDFS.domain, self.CAR.Vehicle))
        self.graph.add((self.CAR.madeBy, RDFS.range, self.CAR.Manufacturer))

        # Data properties
        properties = [
            ('modelName', XSD.string),
            ('modelYear', XSD.integer),
            ('price', XSD.float),
            ('mileage', XSD.float),
            ('safetyRating', XSD.float),
            ('reliabilityScore', XSD.float),
        ]
        for prop_name, dtype in properties:
            prop = self.CAR[prop_name]
            self.graph.add((prop, RDF.type, OWL.DatatypeProperty))
            self.graph.add((prop, RDFS.domain, self.CAR.Vehicle))
            self.graph.add((prop, RDFS.range, dtype))

    def build_from_dataframe(self, df: pd.DataFrame):
        # Add vehicles from dataframe to the graph.
        
        for _, row in df.iterrows():
            self._add_vehicle(row)

        # save to file 
        self.save_ontology()

    def _add_vehicle(self, row):
        # Add a single vehicle to the graph
        # create unique ID for the vehicle
        make = str(row.get('make', 'Unknown')).replace(' ', '_')
        model = str(row.get('model', 'Unknown')).replace(' ', '_')
        year = int(row.get('year', 0))
        vehicle_id = f"{make}_{model}_{year}"

        vehicle_uri = self.CAR[vehicle_id]

        # type assertions
        self.graph.add((vehicle_uri, RDF.type, self.CAR.Vehicle))

        # manufacturer
        mfr_uri = self.CAR[f"Manufacturer_{make}"]
        self.graph.add((mfr_uri, RDF.type, self.CAR.Manufacturer))
        self.graph.add((mfr_uri, RDFS.label, Literal(make)))
        self.graph.add((vehicle_uri, self.CAR.madeBy, mfr_uri))

        # data properties
        self.graph.add((vehicle_uri, self.CAR.modelName,
                       Literal(str(row.get('model', '')), datatype=XSD.string)))
        self.graph.add((vehicle_uri, self.CAR.modelYear,
                       Literal(int(row.get('year', 0)), datatype=XSD.integer)))
        self.graph.add((vehicle_uri, self.CAR.price,
                       Literal(float(row.get('price', 0)), datatype=XSD.float)))
        self.graph.add((vehicle_uri, self.CAR.mileage,
                       Literal(float(row.get('mileage', 0)), datatype=XSD.float)))
        self.graph.add((vehicle_uri, self.CAR.safetyRating,
                       Literal(float(row.get('overall_rating', 3.0)), datatype=XSD.float)))
        self.graph.add((vehicle_uri, self.CAR.reliabilityScore,
                       Literal(float(row.get('reliability_score', 0.5)), datatype=XSD.float)))

    def save_ontology(self, path='ontology/cars.ttl'):
        # Save the graph to a .ttl file
        Path(path).parent.mkdir(exist_ok=True)
        self.graph.serialize(destination=path, format='turtle')

    # SPARQL Queries 
    def query_safe_vehicles(self, min_rating=4.0):
        
        # SPARQL query to find vehicles with high safety ratings
        
        query = f"""
        PREFIX car: <http://example.org/cars#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT ?vehicle ?model ?year ?safety
        WHERE {{
            ?vehicle a car:Vehicle .
            ?vehicle car:modelName ?model .
            ?vehicle car:modelYear ?year .
            ?vehicle car:safetyRating ?safety .
            FILTER(?safety >= {min_rating})
        }}
        ORDER BY DESC(?safety)
        """
        results = self.graph.query(query)
        return [(str(r.model), int(r.year), float(r.safety)) for r in results]

    def query_reliable_manufacturers(self):
        
        # SPARQL query to find manufacturers with reliable vehicles
        # Uses aggregation to find avg reliability per make
        
        query = """
        PREFIX car: <http://example.org/cars#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?make (AVG(?rel) as ?avgReliability)
        WHERE {
            ?vehicle a car:Vehicle .
            ?vehicle car:madeBy ?mfr .
            ?mfr rdfs:label ?make .
            ?vehicle car:reliabilityScore ?rel .
        }
        GROUP BY ?make
        HAVING (AVG(?rel) >= 0.7)
        ORDER BY DESC(?avgReliability)
        """
        results = self.graph.query(query)
        return [str(r.make) for r in results]

    def query_budget_vehicles(self, max_price=20000):
        
        # SPARQL query for affordable vehicles
        
        query = f"""
        PREFIX car: <http://example.org/cars#>

        SELECT ?vehicle ?model ?year ?price ?safety
        WHERE {{
            ?vehicle a car:Vehicle .
            ?vehicle car:modelName ?model .
            ?vehicle car:modelYear ?year .
            ?vehicle car:price ?price .
            ?vehicle car:safetyRating ?safety .
            FILTER(?price <= {max_price})
        }}
        ORDER BY ?price
        LIMIT 20
        """
        results = self.graph.query(query)
        return list(results)

    def query_by_manufacturer(self, make):
        
        # SPARQL query to find all vehicles by a manufacturer
        
        query = f"""
        PREFIX car: <http://example.org/cars#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?model ?year ?price ?safety ?reliability
        WHERE {{
            ?vehicle a car:Vehicle .
            ?vehicle car:madeBy ?mfr .
            ?mfr rdfs:label "{make}" .
            ?vehicle car:modelName ?model .
            ?vehicle car:modelYear ?year .
            ?vehicle car:price ?price .
            ?vehicle car:safetyRating ?safety .
            ?vehicle car:reliabilityScore ?reliability .
        }}
        ORDER BY DESC(?year)
        """
        results = self.graph.query(query)
        return list(results)

    def query_best_value(self, max_price=25000, min_safety=4.0, min_reliability=0.7):
        
        # SPARQL query combining multiple criteria to find best value cars
        
        query = f"""
        PREFIX car: <http://example.org/cars#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?model ?make ?year ?price ?safety ?reliability
        WHERE {{
            ?vehicle a car:Vehicle .
            ?vehicle car:madeBy ?mfr .
            ?mfr rdfs:label ?make .
            ?vehicle car:modelName ?model .
            ?vehicle car:modelYear ?year .
            ?vehicle car:price ?price .
            ?vehicle car:safetyRating ?safety .
            ?vehicle car:reliabilityScore ?reliability .

            FILTER(?price <= {max_price})
            FILTER(?safety >= {min_safety})
            FILTER(?reliability >= {min_reliability})
        }}
        ORDER BY DESC(?safety) DESC(?reliability) ?price
        LIMIT 10
        """
        results = self.graph.query(query)
        return list(results)

    def get_stats(self):
        # Get some basic stats about the graph
        # count vehicles
        vehicle_count = len(list(self.graph.subjects(RDF.type, self.CAR.Vehicle)))

        # count manufacturers
        mfr_count = len(list(self.graph.subjects(RDF.type, self.CAR.Manufacturer)))

        return {
            'total_triples': len(self.graph),
            'vehicles': vehicle_count,
            'manufacturers': mfr_count
        }


# test it out
if __name__ == '__main__':
    onto = CarOntology()

    # sample data
    test_df = pd.DataFrame([
        {'make': 'TOYOTA', 'model': 'Camry', 'year': 2020, 'price': 22000,
         'mileage': 35000, 'overall_rating': 5.0, 'reliability_score': 0.92},
        {'make': 'HONDA', 'model': 'Civic', 'year': 2019, 'price': 18000,
         'mileage': 42000, 'overall_rating': 4.5, 'reliability_score': 0.88},
        {'make': 'BMW', 'model': '328i', 'year': 2017, 'price': 24000,
         'mileage': 55000, 'overall_rating': 4.0, 'reliability_score': 0.65},
        {'make': 'TOYOTA', 'model': 'RAV4', 'year': 2021, 'price': 28000,
         'mileage': 25000, 'overall_rating': 5.0, 'reliability_score': 0.90},
    ])

    onto.build_from_dataframe(test_df)

    print("Ontology Stats:")
    print(onto.get_stats())

    print("\nSafe vehicles (rating >= 4.5):")
    for model, year, safety in onto.query_safe_vehicles(4.5):
        print(f"  {year} {model} - {safety} stars")

    print("\nReliable manufacturers:")
    for make in onto.query_reliable_manufacturers():
        print(f"  {make}")

    print("\nBest value vehicles:")
    for row in onto.query_best_value():
        print(f"  {row.year} {row.make} {row.model} - ${float(row.price):,.0f}")

    print("\nOntology saved to ontology/cars.ttl")
