require 'spec_helper'

RSpec.describe 'Words API' do
  describe 'GET /api/words' do
    it 'returns a list of words' do
      response = HTTParty.get("#{BASE_URL}/api/words")
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to be_an(Array)
      if json.any?
        expect(json.first).to have_key("id")
        expect(json.first).to have_key("english")
        expect(json.first).to have_key("japanese")
        expect(json.first).to have_key("romaji")
      end
    end
  end

  describe 'GET /api/words/:id' do
    it 'returns details of a specific word' do
      word_id = 1 # assuming this id exists for testing
      response = HTTParty.get("#{BASE_URL}/api/words/#{word_id}")
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to have_key("id")
      expect(json).to have_key("english")
      expect(json).to have_key("japanese")
      expect(json).to have_key("romaji")
      expect(json).to have_key("parts")
    end
  end

  # --- Additional CRUD tests for Words API ---

  describe 'POST /api/words' do
    it 'creates a new word' do
      payload = { english: "Test", japanese: "テスト", romaji: "tesuto", parts: {} }
      response = HTTParty.post("#{BASE_URL}/api/words", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(201)
      json = JSON.parse(response.body)
      expect(json).to have_key("id")
      expect(json["english"]).to eq("Test")
      expect(json["japanese"]).to eq("テスト")
      expect(json["romaji"]).to eq("tesuto")
      expect(json).to have_key("parts")
    end
  end

  describe 'PUT /api/words/:id' do
    it 'updates an existing word' do
      payload = { english: "Initial", japanese: "初期", romaji: "shoki", parts: {} }
      create_response = HTTParty.post("#{BASE_URL}/api/words", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      json_create = JSON.parse(create_response.body)
      word_id = json_create["id"]

      update_payload = { english: "Updated" }
      response = HTTParty.put("#{BASE_URL}/api/words/#{word_id}", body: update_payload.to_json, headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(200)
      json_update = JSON.parse(response.body)
      expect(json_update["english"]).to eq("Updated")
    end
  end

  describe 'DELETE /api/words/:id' do
    it 'deletes an existing word' do
      payload = { english: "To Delete", japanese: "削除", romaji: "sakujo", parts: {} }
      create_response = HTTParty.post("#{BASE_URL}/api/words", body: payload.to_json, headers: { 'Content-Type' => 'application/json' })
      json_create = JSON.parse(create_response.body)
      word_id = json_create["id"]

      response = HTTParty.delete("#{BASE_URL}/api/words/#{word_id}")
      expect(response.code).to eq(204)
      get_response = HTTParty.get("#{BASE_URL}/api/words/#{word_id}")
      expect(get_response.code).to eq(404)
    end
  end
end 