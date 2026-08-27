-- SCENARIO: 3-day Denver to Palm Springs travel itinerary for 1 person, Mar 27-29 2022, budget $2200
-- AUTHORED: from intent: "Could you design a 3-day travel itinerary from Denver to Palm Springs for 1 person? The travel should span from March 27th to March 29th, 2022. The travel budget is set at $2,200. No specific local constraints are given."

const query: Artifact;
const outbound_flights: Artifact;
const return_flights: Artifact;
const accommodations: Artifact;
const restaurants: Artifact;
const attractions: Artifact;
const final_plan: Artifact;

const outbound_flight_step: Step;
const return_flight_step: Step;
const accommodation_step: Step;
const restaurant_step: Step;
const attraction_step: Step;
const assembly_step: Step;

const search_agent: Agent, Executor;
const accommodation_agent: Agent, Executor;
const restaurant_agent: Agent, Executor;
const attraction_agent: Agent, Executor;
const assembly_agent: Agent, Executor;

workflow denver_palmsprings_trip {
  -- DATA FLOW
  input_workflow(denver_palmsprings_trip) == [query];
  consumes(outbound_flight_step) == [query];
  produces(outbound_flight_step) == [outbound_flights];
  consumes(return_flight_step) == [query];
  produces(return_flight_step) == [return_flights];
  consumes(accommodation_step) == [query];
  produces(accommodation_step) == [accommodations];
  consumes(restaurant_step) == [query];
  produces(restaurant_step) == [restaurants];
  consumes(attraction_step) == [query];
  produces(attraction_step) == [attractions];
  consumes(assembly_step) == [query, outbound_flights, return_flights, accommodations, restaurants, attractions];
  produces(assembly_step) == [final_plan];
  output_workflow(denver_palmsprings_trip) == [final_plan];

  -- EXECUTOR ASSIGNMENT
  step_executor(outbound_flight_step) == search_agent;
  step_executor(return_flight_step) == search_agent;
  step_executor(accommodation_step) == accommodation_agent;
  step_executor(restaurant_step) == restaurant_agent;
  step_executor(attraction_step) == attraction_agent;
  step_executor(assembly_step) == assembly_agent;

  -- STEP CONFIGURATION
  step_name(outbound_flight_step) == "Search Outbound Flight";
  step_instruction(outbound_flight_step) == "Use the search_flights tool with origin=Denver, destination=Palm Springs, departure_date=2022-03-27. Return every candidate flight exactly as returned by the tool as the outbound_flights artifact. Return only a strict JSON object keyed by outbound_flights, no prose.";
  step_timeout(outbound_flight_step) == 300;
  step_name(return_flight_step) == "Search Return Flight";
  step_instruction(return_flight_step) == "Use the search_flights tool with origin=Palm Springs, destination=Denver, departure_date=2022-03-29. Return every candidate flight exactly as returned by the tool as the return_flights artifact. Return only a strict JSON object keyed by return_flights, no prose.";
  step_timeout(return_flight_step) == 300;
  step_name(accommodation_step) == "Search Accommodations";
  step_instruction(accommodation_step) == "Use the search_accommodations tool with city=Palm Springs. Return every candidate accommodation exactly as returned by the tool as the accommodations artifact. Return only a strict JSON object keyed by accommodations, no prose.";
  step_timeout(accommodation_step) == 300;
  step_name(restaurant_step) == "Search Restaurants";
  step_instruction(restaurant_step) == "Use the search_restaurants tool with city=Palm Springs. Return every candidate restaurant exactly as returned by the tool as the restaurants artifact. Return only a strict JSON object keyed by restaurants, no prose.";
  step_timeout(restaurant_step) == 300;
  step_name(attraction_step) == "Search Attractions";
  step_instruction(attraction_step) == "Use the search_attractions tool with city=Palm Springs. Return every candidate attraction exactly as returned by the tool as the attractions artifact. Return only a strict JSON object keyed by attractions, no prose.";
  step_timeout(attraction_step) == 300;
  step_name(assembly_step) == "Assemble Itinerary";
  step_instruction(assembly_step) == "Build the complete 3-day itinerary JSON object for the query. Trip: Denver to Palm Springs for 1 traveler, March 27 to March 29 2022, total budget 2200 USD. Requirements: choose one outbound flight on March 27 from Denver to Palm Springs and one return flight on March 29 from Palm Springs to Denver from the flight artifacts; choose one accommodation in Palm Springs for two nights and list that same accommodation on days 1 and 2; choose restaurants and attractions in Palm Springs for each day. Compute the total cost exactly as: outbound flight price + return flight price + accommodation price multiplied by 2 nights + sum of every meal price (breakfast, lunch, dinner) across all days, using the price fields in the consumed artifacts. The total must be at or below 2200 with margin; if the initially chosen accommodation makes the total exceed the budget, switch to the cheapest accommodation option in the accommodation artifact so the total stays within budget. Return ONLY a strict JSON object with exactly these keys: idx (integer 18), query (the exact original user query string from the query artifact, copied verbatim), plan (array of three day objects). Each day object must have fields: day (1-indexed integer), current_city (day 1: from Denver to Palm Springs; day 2: Palm Springs; day 3: from Palm Springs to Denver), transportation (exact flight info string from the tool, or - if none), breakfast (Name, City or -), lunch (Name, City or -), dinner (Name, City or -), attraction (semicolon-separated Name, City; entries or -), accommodation (Name, City or -). Use only real data from the consumed artifacts. Do not include any text outside the JSON.";
  step_timeout(assembly_step) == 600;

  -- WORKFLOW CONFIGURATION
  max_concurrency(denver_palmsprings_trip) == 5;
  workflow_timeout(denver_palmsprings_trip) == 1800;
}
