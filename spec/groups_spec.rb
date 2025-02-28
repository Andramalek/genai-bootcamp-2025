require 'spec_helper'

RSpec.describe 'Groups API' do
  describe 'GET /api/groups' do
    it 'returns a list of groups' do
      response = HTTParty.get("#{BASE_URL}/api/groups")
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to be_an(Array)
      if json.any?
        expect(json.first).to have_key("id")
        expect(json.first).to have_key("name")
      end
    end
  end

  describe 'GET /api/groups/:id' do
    it 'returns details of a specific group' do
      # Create a group first so that it exists
      payload = { name: "Existing Group" }
      create_response = HTTParty.post("#{BASE_URL}/api/groups", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      expect(create_response.code).to eq(201)
      json_create = JSON.parse(create_response.body)
      group_id = json_create["id"]

      # Now fetch the created group
      response = HTTParty.get("#{BASE_URL}/api/groups/#{group_id}")
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to have_key("id")
      expect(json).to have_key("name")
    end
  end

  # --- Additional CRUD tests for Groups API ---

  describe 'POST /api/groups' do
    it 'creates a new group' do
      payload = { name: "New Group" }
      response = HTTParty.post("#{BASE_URL}/api/groups", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(201)
      json = JSON.parse(response.body)
      expect(json).to have_key("id")
      expect(json["name"]).to eq("New Group")
    end
  end

  describe 'PUT /api/groups/:id' do
    it 'updates an existing group' do
      payload = { name: "Group To Update" }
      create_response = HTTParty.post("#{BASE_URL}/api/groups", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      json_create = JSON.parse(create_response.body)
      group_id = json_create["id"]

      update_payload = { name: "Updated Group" }
      response = HTTParty.put("#{BASE_URL}/api/groups/#{group_id}", body: update_payload.to_json, headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(200)
      json_update = JSON.parse(response.body)
      expect(json_update["name"]).to eq("Updated Group")
    end
  end

  describe 'DELETE /api/groups/:id' do
    it 'deletes an existing group' do
      payload = { name: "Group To Delete" }
      create_response = HTTParty.post("#{BASE_URL}/api/groups", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      json_create = JSON.parse(create_response.body)
      group_id = json_create["id"]

      response = HTTParty.delete("#{BASE_URL}/api/groups/#{group_id}")
      expect(response.code).to eq(204)
      get_response = HTTParty.get("#{BASE_URL}/api/groups/#{group_id}")
      expect(get_response.code).to eq(404)
    end
  end
end 