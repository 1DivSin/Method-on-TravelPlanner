-- SCENARIO: TravelPlanner trip plan from Minneapolis to Seattle, 3 days (2022-03-29 to 2022-03-31), budget $1,800
-- AUTHORED: from intent: "Please create a travel plan departing from Minneapolis and heading to Seattle for 3 days, from March 29th to March 31st, 2022, with a budget of $1,800."

const query: Artifact;
const flight_results: Artifact;
const accommodation_results: Artifact;
const restaurant_results: Artifact;
const attraction_results: Artifact;
const final_plan: Artifact;

const search_flights_step: Step;
const search_accommodations_step: Step;
const search_restaurants_step: Step;
const search_attractions_step: Step;
const assemble_plan_step: Step;

const flight_searcher: Agent, Executor;
const accommodation_searcher: Agent, Executor;
const restaurant_searcher: Agent, Executor;
const attraction_searcher: Agent, Executor;
const trip_planner: Agent, Executor;

workflow seattle_trip_planner {
  -- DATA FLOW
  input_workflow(seattle_trip_planner) == [query];
  consumes(search_flights_step) == [query];
  produces(search_flights_step) == [flight_results];
  consumes(search_accommodations_step) == [query];
  produces(search_accommodations_step) == [accommodation_results];
  consumes(search_restaurants_step) == [query];
  produces(search_restaurants_step) == [restaurant_results];
  consumes(search_attractions_step) == [query];
  produces(search_attractions_step) == [attraction_results];
  consumes(assemble_plan_step) == [flight_results, accommodation_results, restaurant_results, attraction_results];
  produces(assemble_plan_step) == [final_plan];
  output_workflow(seattle_trip_planner) == [final_plan];

  -- EXECUTOR ASSIGNMENT
  step_executor(search_flights_step) == flight_searcher;
  step_executor(search_accommodations_step) == accommodation_searcher;
  step_executor(search_restaurants_step) == restaurant_searcher;
  step_executor(search_attractions_step) == attraction_searcher;
  step_executor(assemble_plan_step) == trip_planner;

  -- STEP CONFIGURATION
  step_name(search_flights_step) == "Search Flights";
  step_instruction(search_flights_step) == "Read the query artifact, which contains the user travel request. The trip departs from Minneapolis and heads to Seattle, March 29 to March 31, 2022. Call the search_flights tool twice: first with origin Minneapolis, destination Seattle, departure_date 2022-03-29 for the outbound leg; then with origin Seattle, destination Minneapolis, departure_date 2022-03-31 for the return leg. Return one strict JSON object keyed by the output artifact ID: {\"flight_results\": {\"outbound\": [<each flight record verbatim from the first call>], \"return\": [<each flight record verbatim from the second call>]}}. Preserve every field the tool returns for each flight (Flight Number, Price, DepTime, ArrTime, ActualElapsedTime, FlightDate, OriginCityName, DestCityName, Distance).";
  step_timeout(search_flights_step) == 300;

  step_name(search_accommodations_step) == "Search Accommodations";
  step_instruction(search_accommodations_step) == "Read the query artifact, which contains the user travel request. The trip stays in Seattle from March 29 to March 31, 2022 (3 nights). Call the search_accommodations tool with city Seattle. Return one strict JSON object keyed by the output artifact ID: {\"accommodation_results\": [<every accommodation record verbatim from the tool>]}. Preserve every field the tool returns for each accommodation (NAME, price, room type, house_rules, minimum nights, maximum occupancy, review rate number, city).";
  step_timeout(search_accommodations_step) == 300;

  step_name(search_restaurants_step) == "Search Restaurants";
  step_instruction(search_restaurants_step) == "Read the query artifact, which contains the user travel request. The trip spends March 29 to March 31, 2022 in Seattle. Call the search_restaurants tool with city Seattle. Return one strict JSON object keyed by the output artifact ID: {\"restaurant_results\": [<every restaurant record verbatim from the tool>]}. Preserve every field the tool returns (Name, Average Cost, Cuisines, Aggregate Rating, City).";
  step_timeout(search_restaurants_step) == 300;

  step_name(search_attractions_step) == "Search Attractions";
  step_instruction(search_attractions_step) == "Read the query artifact, which contains the user travel request. The trip spends March 29 to March 31, 2022 in Seattle. Call the search_attractions tool with city Seattle. Return one strict JSON object keyed by the output artifact ID: {\"attraction_results\": [<every attraction record verbatim from the tool>]}. Preserve every field the tool returns (Name, Latitude, Longitude, Address, Phone, Website, City).";
  step_timeout(search_attractions_step) == 300;

  step_name(assemble_plan_step) == "Assemble Trip Plan";
  step_instruction(assemble_plan_step) == "You are the final assembler for a travel planning task. The user query is: \"Please create a travel plan departing from Minneapolis and heading to Seattle for 3 days, from March 29th to March 31st, 2022, with a budget of $1,800.\" Consume the four search artifacts: flight_results (an object with outbound and return flight lists), accommodation_results, restaurant_results, attraction_results. Build a complete 3-day itinerary for 1 traveler. Constraints: the total cost must not exceed $1,800; the accommodation must be in Seattle, be usable for a 3-night stay (minimum nights <= 3 and maximum occupancy >= 1); attractions in this dataset have no listed price and cost $0. Select exactly one outbound flight for day 1 (2022-03-29) and exactly one return flight for day 3 (2022-03-31); day 2 has no travel. Choose one accommodation used for all 3 nights, and choose restaurants and attractions for each day from the provided lists. Total cost = outbound flight Price + return flight Price + 3 x accommodation price + sum of every chosen restaurant Average Cost (attractions cost 0); keep the total at or under $1,800. Return one strict JSON object keyed by the output artifact ID \"final_plan\" whose value is exactly: {\"idx\": 11, \"query\": \"Please create a travel plan departing from Minneapolis and heading to Seattle for 3 days, from March 29th to March 31st, 2022, with a budget of $1,800.\", \"plan\": [<one object per day>]}. Each day object has only these fields: day (1, 2, 3), current_city, transportation, breakfast, attraction, lunch, dinner, accommodation. Day 1 current_city = \"from Minneapolis to Seattle\"; day 2 current_city = \"Seattle\"; day 3 current_city = \"from Seattle to Minneapolis\". transportation uses exactly the format \"Flight Number: <Flight Number>, from <OriginCityName> to <DestCityName>, Departure Time: <DepTime>, Arrival Time: <ArrTime>\" on travel days and \"-\" otherwise. breakfast, lunch, dinner are \"<Restaurant Name>, Seattle\" or \"-\" when not applicable. attraction is a semicolon-separated list such as \"<Attraction Name>, Seattle;<Another Attraction Name>, Seattle;\" or \"-\". accommodation is \"<Accommodation NAME>, Seattle\" on every day. Do not include any fields beyond those listed and do not add explanation.";
  step_timeout(assemble_plan_step) == 600;

  -- WORKFLOW CONFIGURATION
  max_concurrency(seattle_trip_planner) == 4;
  workflow_timeout(seattle_trip_planner) == 1200;
}
