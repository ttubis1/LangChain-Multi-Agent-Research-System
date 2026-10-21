from src.agents.agents import (
    build_search_agent, 
    build_reader_agent, 
    writer_chain, 
    critic_chain, 
    refiner_chain
)
from langchain_core.messages import HumanMessage

def run_research_pipeline(topic: str) -> dict:
    state = {}

    # Step 1: Search Agent
    print("\n" + " ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [HumanMessage(content=f"Find recent, reliable and detailed information about: {topic}")]
    })
    state["search_results"] = search_result['messages'][-1].content
    print("\nsearch result:\n", state['search_results'])

    # Step 2: Reader Agent (Scraping)
    print("\n" + " ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [
            HumanMessage(
                content=(
                    f"Based on the following search results about '{topic}', "
                    f"pick the most relevant URL and scrape it for deeper content.\n\n"
                    f"Search Results:\n{state['search_results'][:800]}"
                )
            )
        ]
    })
    state['scraped_content'] = reader_result['messages'][-1].content
    print("\nscraped content:\n", state['scraped_content'])

    # Step 3: Writer Chain
    print("\n" + " ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })
    print("\nInitial Draft Report:\n", state['report'])

    # Step 4: Critic Chain
    print("\n" + " ="*50)
    print("step 4 - Critic is reviewing the report ...")
    print("="*50)

    state["feedback"] = critic_chain.invoke({
        "report": state['report']
    })
    print("\ncritic report:\n", state['feedback'])

    # Step 5: Refiner Chain
    print("\n" + " ="*50)
    print("step 5 - Refiner is improving the report ...")
    print("="*50)

    state["final_report"] = refiner_chain.invoke({
        "topic": topic,
        "report": state["report"],
        "critic_feedback": state["feedback"]
    })
    print("\nFinal Improved Report:\n", state['final_report'])

    return state

