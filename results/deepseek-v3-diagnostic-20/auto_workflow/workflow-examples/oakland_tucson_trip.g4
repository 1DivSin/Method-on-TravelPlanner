-- SCENARIO: Build a 3-day Oakland -> Tucson itinerary for one person, Mar 15-17 2022, within a $1,400 budget
-- AUTHORED: travel planning workflow using parallel TravelPlanner searches and one sequential assembly step

const trip_request: Artifact;
const flights_outbound: Artifact;
const flights_return: Artifact;
const accommodations: Artifact;
const restaurants: Artifact;
const attractions: Artifact;
const final_plan: Artifact;

const search_flights_out: Step;
const search_flights_back: Step;
const search_accommodations_step: Step;
const search_restaurants_step: Step;
const search_attractions_step: Step;
const assemble_plan: Step;

const flights_agent: Agent, Executor;
const accommodation_agent: Agent, Executor;
const restaurant_agent: Agent, Executor;
const attraction_agent: Agent, Executor;
const assembly_agent: Agent, Executor;

workflow oakland_tucson_trip {
  -- DATA FLOW
  input_workflow(oakland_tucson_trip) == [trip_request];
  consumes(search_flights_out) == [trip_request];
  produces(search_flights_out) == [flights_outbound];
  consumes(search_flights_back) == [trip_request];
  produces(search_flights_back) == [flights_return];
  consumes(search_accommodations_step) == [trip_request];
  produces(search_accommodations_step) == [accommodations];
  consumes(search_restaurants_step) == [trip_request];
  produces(search_restaurants_step) == [restaurants];
  consumes(search_attractions_step) == [trip_request];
  produces(search_attractions_step) == [attractions];
  consumes(assemble_plan) == [trip_request, flights_outbound, flights_return, accommodations, restaurants, attractions];
  produces(assemble_plan) == [final_plan];
  output_workflow(oakland_tucson_trip) == [final_plan];

  -- EXECUTOR ASSIGNMENT
  step_executor(search_flights_out) == flights_agent;
  step_executor(search_flights_back) == flights_agent;
  step_executor(search_accommodations_step) == accommodation_agent;
  step_executor(search_restaurants_step) == restaurant_agent;
  step_executor(search_attractions_step) == attraction_agent;
  step_executor(assemble_plan) == assembly_agent;

  -- STEP CONFIGURATION
  step_name(search_flights_out) == "Search Outbound Flights";
  step_instruction(search_flights_out) == "You are a TravelPlanner search agent. Read the consumed trip_request artifact (origin Oakland, destination Tucson, departure date 2022-03-15). Call the search_flights tool with origin Oakland, destination Tucson, departure_date 2022-03-15, and capture the complete official candidate list exactly as the tool returns it. Return exactly one strict JSON object {\"flights_outbound\": <array>} whose value is the full list of candidate flights returned by the tool, preserving every field (Flight Number, Price, DepTime, ArrTime, FlightDate, OriginCityName, DestCityName) verbatim. Do not invent or modify any flight; do not put the result in prose.";
  step_timeout(search_flights_out) == 300;

  step_name(search_flights_back) == "Search Return Flights";
  step_instruction(search_flights_back) == "You are a TravelPlanner search agent. Read the consumed trip_request artifact (origin Oakland, destination Tucson, return date 2022-03-17). Call the search_flights tool with origin Tucson, destination Oakland, departure_date 2022-03-17, and capture the complete official candidate list exactly as the tool returns it. If the tool reports that no flight exists, return {\"flights_return\": []}. Return exactly one strict JSON object {\"flights_return\": <array>} whose value is the full list of candidate flights returned by the tool, preserving every field (Flight Number, Price, DepTime, ArrTime, FlightDate, OriginCityName, DestCityName) verbatim. Do not invent or modify any flight; do not put the result in prose.";
  step_timeout(search_flights_back) == 300;

  step_name(search_accommodations_step) == "Search Tucson Accommodations";
  step_instruction(search_accommodations_step) == "You are a TravelPlanner search agent. Read the consumed trip_request artifact (destination city Tucson). Call the search_accommodations tool with city Tucson and capture the complete official candidate list exactly as the tool returns it. Return exactly one strict JSON object {\"accommodations\": <array>} whose value is the full list of accommodation candidates returned by the tool, preserving every field (NAME, price, room type, minimum nights, maximum occupancy, city) verbatim. Do not invent or modify any entry; do not put the result in prose.";
  step_timeout(search_accommodations_step) == 300;

  step_name(search_restaurants_step) == "Search Tucson Restaurants";
  step_instruction(search_restaurants_step) == "You are a TravelPlanner search agent. Read the consumed trip_request artifact (destination city Tucson). Call the search_restaurants tool with city Tucson and capture the complete official candidate list exactly as the tool returns it. Return exactly one strict JSON object {\"restaurants\": <array>} whose value is the full list of restaurant candidates returned by the tool, preserving every field (Name, Average Cost, Cuisines, City) verbatim. Do not invent or modify any entry; do not put the result in prose.";
  step_timeout(search_restaurants_step) == 300;

  step_name(search_attractions_step) == "Search Tucson Attractions";
  step_instruction(search_attractions_step) == "You are a TravelPlanner search agent. Read the consumed trip_request artifact (destination city Tucson). Call the search_attractions tool with city Tucson and capture the complete official candidate list exactly as the tool returns it. Return exactly one strict JSON object {\"attractions\": <array>} whose value is the full list of attraction candidates returned by the tool, preserving every field (Name, City, etc.) verbatim. Do not invent or modify any entry; do not put the result in prose.";
  step_timeout(search_attractions_step) == 300;

  step_name(assemble_plan) == "Assemble Final Itinerary";
  step_instruction(assemble_plan) == "You are a travel planning assembler. Build the final 3-day itinerary from the consumed artifacts using ONLY candidates that actually appear in the consumed search results (flights_outbound, flights_return, accommodations, restaurants, attractions). trip_request specifies: one traveler, origin Oakland, destination Tucson, dates 2022-03-15 to 2022-03-17, total budget $1,400. Structure: Day 1 (Mar 15) current_city 'from Oakland to Tucson' with the outbound flight; Day 2 (Mar 16) current_city 'Tucson' with transportation '-'; Day 3 (Mar 17) current_city 'from Tucson to Oakland'. Select the outbound flight from flights_outbound for Day 1 transportation using the exact tool format: 'Flight Number: <Flight Number>, from <OriginCityName> to <DestCityName>, Departure Time: <DepTime>, Arrival Time: <ArrTime>'. For Day 3 transportation: if flights_return contains a flight, use the same exact tool format for it; otherwise (empty list) set Day 3 transportation to '-'. Accommodation: choose one Tucson accommodation from accommodations that satisfies minimum nights <= 2 and maximum occupancy >= 1 for the 2 nights of Mar 15 and Mar 16; list it on Day 1 and Day 2, and set Day 3 accommodation to '-'. Every accommodation value MUST be formatted as '<NAME>, <city>' (e.g. 'Private room with private bathroom, Tucson') - never omit the city. Meals: breakfast/lunch/dinner each formatted '<Name>, <City>' or '-'; every meal must come from the restaurants artifact and be a real candidate name with its city. Attractions: semicolon-separated '<Name>, <City>;' entries using only Tucson attractions from the attractions artifact, or '-'. Total cost for one person = outbound flight price + return flight price (if used) + accommodation price x 2 nights + all listed meal Average Costs + all listed attraction costs; the total MUST NOT exceed $1,400. Return exactly one strict JSON object {\"final_plan\": {\"idx\": 2, \"query\": \"<the exact query text from the trip_request artifact>\", \"plan\": [{\"day\": 1, \"current_city\": \"from Oakland to Tucson\", \"transportation\": \"<flight string>\", \"breakfast\": \"<Name>, <City>\", \"attraction\": \"<Name>, <City>;\", \"lunch\": \"<Name>, <City>\", \"dinner\": \"<Name>, <City>\", \"accommodation\": \"<NAME>, <city>\"}, {\"day\": 2, \"current_city\": \"Tucson\", \"transportation\": \"-\", ...}, {\"day\": 3, \"current_city\": \"from Tucson to Oakland\", \"transportation\": \"<flight string or ->\", ...}]}} with every field present on every day object and exactly the required JSON shape. Do not add any explanation outside the JSON.";
  step_timeout(assemble_plan) == 600;

  -- WORKFLOW CONFIGURATION
  max_concurrency(oakland_tucson_trip) == 5;
  workflow_timeout(oakland_tucson_trip) == 1200;
}
