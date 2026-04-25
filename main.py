# main.py
from workers.gpu_worker import GPUWorker
from lb.load_balancer import LoadBalancer
from master.scheduler import Scheduler
from client.load_generator import run_load_test
from rag.retriever import retrieve_context

def main():
    # # Create GPU workers
    # workers = [GPUWorker(i) for i in range(4)] # simulate 4 GPUs
    
    # # Load Balancer
    # lb = LoadBalancer(workers)
    
    # # Scheduler
    # scheduler = Scheduler(lb)
    
    # # Run simulation
    # run_load_test(scheduler, num_users=1000)
    query_1 = "what is utilization rule"
    context_1 = retrieve_context(query_1)

    print(f"Query: {query_1}")
    print(f"Retrieved Context: {context_1[:500].encode('ascii', 'ignore').decode('ascii')}...")
    print("-" * 30)

    # Test Query 2: Something NOT in the PDF
    query_2 = "how do cluster computing work"
    context_2 = retrieve_context(query_2)

    print(f"Query: {query_2}")
    print(f"Retrieved Context: {context_2[:500].encode('ascii', 'ignore').decode('ascii')}...")

if __name__ == "__main__":
    main()