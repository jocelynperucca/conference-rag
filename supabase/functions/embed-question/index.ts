// embed-question: turns a user's question into a 1,536-number embedding.
//
// Browser --(question + login JWT)--> this function --(secret key)--> OpenAI
//
// Request:  POST { "question": "How can I find peace?" }
// Response: 200  { "embedding": [0.032, 0.0045, ...] }
import { corsHeaders, jsonResponse } from "../_shared/cors.ts";
import { getUser } from "../_shared/auth.ts";

const MAX_QUESTION_LENGTH = 1000;

Deno.serve(async (req: Request) => {
  // TODO 2: CORS preflight.
  //   If req.method is "OPTIONS", return an empty response ("ok") with
  //   corsHeaders(req) as its headers -- and do nothing else.
  //   Hint: new Response("ok", { headers: ... })

  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders(req) });
  }

  try {
    // TODO 3: Auth check.
    //   Call getUser(req). If there's no user, return
    //   jsonResponse(req, { error: "..." }, 401) with a helpful message.
    //   Question to consider: why must this happen BEFORE calling OpenAI?

    const user = await getUser(req);
    if (!user) {
      return jsonResponse(req, { error: "user not authenticated" }, 401);
    }

    // TODO 4: Read and validate the question.
    //   - Parse the body: const { question } = await req.json();
    //   - If question isn't a non-empty string -> 400 error
    //   - If it's longer than MAX_QUESTION_LENGTH -> 400 error

    const { question } = await req.json();
    if (typeof question !== "string" || question.trim() === "") {
      return jsonResponse(req, { error: "no question" }, 400);
    } else if (question.length > MAX_QUESTION_LENGTH) {
      return jsonResponse(req, { error: "too long question" }, 400);
    }

    // TODO 5: Call OpenAI's embeddings endpoint.
    //   - Get the key: Deno.env.get("OPENAI_API_KEY")
    //   - fetch("https://api.openai.com/v1/embeddings", { method: "POST", headers, body })
    //       headers: Authorization: `Bearer ${key}`, Content-Type: application/json
    //       body:    JSON.stringify({ model: "text-embedding-3-small", input: question })
    //     It MUST be the same model the Python script used -- why?
    //   - If the response isn't ok (!res.ok), return a 502 error.
    //   - The vector is at: (await res.json()).data[0].embedding

    const key = Deno.env.get("OPENAI_API_KEY");
    const res = await fetch("https://api.openai.com/v1/embeddings", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "text-embedding-3-small",
        input: question,
      }),
    });

    if (!res.ok) {
      return jsonResponse(req, { error: "bad response" }, 502);
    }

    const embedding = (await res.json()).data[0].embedding;
    // TODO 6: Return { embedding } with status 200 using jsonResponse.
    return jsonResponse(req, { embedding }, 200);
  } catch (err) {
    // Anything unexpected (e.g. body isn't valid JSON) ends up here.
    console.error(err);
    return jsonResponse(req, { error: "Internal error" }, 500);
  }
});
