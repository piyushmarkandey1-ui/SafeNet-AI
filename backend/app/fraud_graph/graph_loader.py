"""
SafeNet AI — Graph Loader (In-Memory NetworkX)

Ingests synthetic transactions and call records into a NetworkX MultiDiGraph.
Provides methods to identify connected components (mule rings) and high-risk nodes.
"""
import networkx as nx
import pandas as pd
import os

class FraudGraph:
    def __init__(self):
        # MultiDiGraph allows multiple edges between same nodes (e.g., multiple calls)
        self.G = nx.MultiDiGraph()
        
    def load_call_records(self, csv_path):
        if not os.path.exists(csv_path):
            print(f"Warning: {csv_path} not found.")
            return
            
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            caller = row['caller_number']
            callee = row['callee_number']
            
            # Add nodes if they don't exist
            self.G.add_node(caller, type='PhoneNumber')
            self.G.add_node(callee, type='PhoneNumber')
            
            # Add directed edge
            self.G.add_edge(
                caller, callee, 
                edge_type='CALLED',
                duration=row['duration_sec'],
                is_spoofed=row['is_spoofed'],
                timestamp=row['timestamp'],
                transcript_snippet=row['transcript_snippet']
            )

    def load_transactions(self, csv_path):
        if not os.path.exists(csv_path):
            print(f"Warning: {csv_path} not found.")
            return
            
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            sender = row['sender_account']
            receiver = row['receiver_account']
            device = row['device_hash']
            
            self.G.add_node(sender, type='BankAccount')
            self.G.add_node(receiver, type='BankAccount')
            self.G.add_node(device, type='Device')
            
            # Edges between accounts
            self.G.add_edge(
                sender, receiver,
                edge_type='TRANSFERRED_TO',
                amount=row['amount'],
                timestamp=row['timestamp'],
                flagged_mule=row['flagged_mule']
            )
            
            # Edge linking accounts to devices
            self.G.add_edge(sender, device, edge_type='SHARED_DEVICE')
            
    def summary(self):
        print("\n--- Fraud Graph Summary ---")
        print(f"Total Nodes: {self.G.number_of_nodes()}")
        print(f"Total Edges: {self.G.number_of_edges()}")
        
        # Count node types
        types = {}
        for _, data in self.G.nodes(data=True):
            t = data.get('type', 'Unknown')
            types[t] = types.get(t, 0) + 1
            
        print("\nNode Types:")
        for t, count in types.items():
            print(f"  - {t}: {count}")
            
        # Count edge types
        e_types = {}
        for _, _, data in self.G.edges(data=True):
            t = data.get('edge_type', 'Unknown')
            e_types[t] = e_types.get(t, 0) + 1
            
        print("\nEdge Types:")
        for t, count in e_types.items():
            print(f"  - {t}: {count}")

        # Highlight highest degree nodes (potential central hubs/mules)
        if self.G.number_of_nodes() > 0:
            degrees = sorted(self.G.in_degree(), key=lambda x: x[1], reverse=True)[:5]
            print("\nTop 5 Nodes by In-Degree (Potential Receivers/Mules):")
            for node, degree in degrees:
                n_type = self.G.nodes[node].get('type', 'Unknown')
                print(f"  - {node} ({n_type}): {degree} incoming edges")
        print("---------------------------\n")

if __name__ == "__main__":
    graph = FraudGraph()
    # Paths assume running from backend directory
    graph.load_call_records("../data/synthetic/calls_SYNTHETIC.csv")
    graph.load_transactions("../data/synthetic/transactions_SYNTHETIC.csv")
    graph.summary()
