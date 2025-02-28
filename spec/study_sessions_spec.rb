require 'spec_helper'

RSpec.describe 'Study Sessions API' do
  describe 'GET /api/study_sessions' do
    it 'returns a list of study sessions' do
      response = HTTParty.get("#{BASE_URL}/api/study_sessions")
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to be_an(Array)
      if json.any?
        expect(json.first).to have_key("id")
        expect(json.first).to have_key("created_at")
        expect(json.first).to have_key("group_id")
        expect(json.first).to have_key("study_activity_id")
      end
    end
  end

  describe 'GET /api/study_sessions/:id' do
    it 'returns details of a specific study session' do
      session_id = 1 # assuming a study session with id 1 exists
      response = HTTParty.get("#{BASE_URL}/api/study_sessions/#{session_id}")
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to have_key("id")
      expect(json).to have_key("created_at")
      expect(json).to have_key("group_id")
      expect(json).to have_key("study_activity_id")
    end
  end

  describe 'GET /api/study_sessions/:id/words' do
    it 'returns words for a specific study session' do
      session_id = 1 # assuming study session with id 1 exists
      response = HTTParty.get("#{BASE_URL}/api/study_sessions/#{session_id}/words")
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to be_an(Array)
      if json.any?
        expect(json.first).to have_key("id")
        expect(json.first).to have_key("english")
      end
    end
  end

  # --- Additional CRUD tests for Study Sessions API ---

  describe 'POST /api/study_sessions' do
    it 'creates a new study session' do
      payload = { group_id: 1, study_activity_id: 1 }
      response = HTTParty.post("#{BASE_URL}/api/study_sessions", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(201)
      json = JSON.parse(response.body)
      expect(json).to have_key("id")
      expect(json).to have_key("created_at")
      expect(json["group_id"]).to eq(payload[:group_id])
      expect(json["study_activity_id"]).to eq(payload[:study_activity_id])
    end
  end

  describe 'PUT /api/study_sessions/:id' do
    it 'updates an existing study session' do
      payload = { group_id: 1, study_activity_id: 1 }
      create_response = HTTParty.post("#{BASE_URL}/api/study_sessions", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      json_create = JSON.parse(create_response.body)
      session_id = json_create["id"]

      update_payload = { study_activity_id: 2 }
      response = HTTParty.put("#{BASE_URL}/api/study_sessions/#{session_id}", body: update_payload.to_json, headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(200)
      json_update = JSON.parse(response.body)
      expect(json_update["study_activity_id"]).to eq(update_payload[:study_activity_id])
    end
  end

  describe 'DELETE /api/study_sessions/:id' do
    it 'deletes an existing study session' do
      payload = { group_id: 1, study_activity_id: 1 }
      create_response = HTTParty.post("#{BASE_URL}/api/study_sessions", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      json_create = JSON.parse(create_response.body)
      session_id = json_create["id"]

      response = HTTParty.delete("#{BASE_URL}/api/study_sessions/#{session_id}")
      expect(response.code).to eq(204)
      get_response = HTTParty.get("#{BASE_URL}/api/study_sessions/#{session_id}")
      expect(get_response.code).to eq(404)
    end
  end
end 