class AIAgentFriend:
    """
    A skeleton implementation of a multimodal AI agent friend.
    
    This class outlines the key components needed to build an empathetic conversational agent capable of
    processing text, audio, and image inputs, and responding with supportive conversation, recommendations,
    and other user-centric functions. Most methods are placeholders designed for integration with actual
    models or APIs (e.g., speech recognition, image captioning, LLMs). The agent maintains a simple
    conversation history and includes basic sentiment-aware response logic as an illustrative example.
    """

    def __init__(self):
        # Conversation history to maintain context
        self.history = []
        # Simple lists of keywords for sentiment analysis (example only)
        self.positive_keywords = {"happy", "good", "great", "excited", "love"}
        self.negative_keywords = {"sad", "bad", "tired", "lonely", "stressed", "depressed"}

    def handle_text(self, text_input: str) -> str:
        """
        Process a text input from the user and generate a response.

        Args:
            text_input (str): The user's message in text form.
        Returns:
            str: Agent's response in text form.
        """
        # Append to history
        self.history.append(("user", text_input))
        # Determine sentiment
        sentiment = self._classify_sentiment(text_input)
        # Generate a response based on sentiment
        if sentiment == "negative":
            response = self._generate_empathy_response(text_input)
        elif sentiment == "positive":
            response = self._generate_celebratory_response(text_input)
        else:
            response = self._generate_neutral_response(text_input)
        # Append agent's response to history
        self.history.append(("agent", response))
        return response

    def handle_audio(self, audio_path: str) -> str:
        """
        Placeholder for processing an audio input. In a full implementation, this method would
        transcribe the audio to text using a speech recognition library or API, then pass the
        transcription to `handle_text` for response generation.

        Args:
            audio_path (str): Path to the audio file containing the user's speech.
        Returns:
            str: Agent's response in text form.
        """
        # TODO: Integrate with speech recognition to convert audio to text
        transcript = "[audio transcription goes here]"
        return self.handle_text(transcript)

    def handle_image(self, image_path: str) -> str:
        """
        Placeholder for processing an image input. A full implementation might use an image captioning
        or classification model to describe the image, then incorporate the description into
        a conversational response.

        Args:
            image_path (str): Path to the image file provided by the user.
        Returns:
            str: Agent's response in text form.
        """
        # TODO: Integrate with an image captioning model to generate captions
        caption = "[image description goes here]"
        return self.handle_text(caption)

    def recommend_activity(self, preference: str = "") -> str:
        """
        Provide a recommendation for food, hobby, or places to visit based on the user's preference.
        In a full implementation, this method would integrate with external recommendation APIs
        or databases. Here we provide a simple rule-based example.

        Args:
            preference (str): User's stated preference or category (e.g., "food", "hobby", "travel").
        Returns:
            str: Recommendation message.
        """
        if not preference:
            return "어떤 추천을 원하시나요? 음식, 취미, 혹은 여행지 중에서 선택해 주세요."
        preference = preference.lower()
        if "food" in preference or "음식" in preference:
            return "오늘은 따뜻한 국수나 향긋한 비빔밥을 드셔보는 건 어떨까요?"
        if "hobby" in preference or "취미" in preference:
            return "최근 인기를 끌고 있는 도자기 공예를 배우거나, 가까운 공원에서 사진을 찍어보는 건 어떨까요?"
        if "travel" in preference or "여행" in preference or "place" in preference or "놀러갈" in preference:
            return "주말에 가까운 한강공원이나 주변 산책길을 걸으며 힐링하는 시간을 가져보세요."
        return "추천이 필요하시면 조금 더 구체적인 관심사를 알려주세요."

    def _classify_sentiment(self, text: str) -> str:
        """
        Simple heuristic sentiment classification based on keyword matching. Real implementations
        should use a proper sentiment analysis model.

        Args:
            text (str): Input text to classify.
        Returns:
            str: "positive", "negative", or "neutral".
        """
        words = set(word.strip('!.,?').lower() for word in text.split())
        if words & self.negative_keywords:
            return "negative"
        if words & self.positive_keywords:
            return "positive"
        return "neutral"

    def _generate_empathy_response(self, text: str) -> str:
        """
        Generate an empathetic response when the user expresses negative sentiment.

        Args:
            text (str): Original user input.
        Returns:
            str: Empathetic response.
        """
        return (
            "요즘 많이 힘드신가 보군요. 제가 옆에서 함께 이야기를 들으며 도와드릴 수 있도록 노력할게요. "
            "때로는 쉬어가는 것도 중요해요. 잠시 산책을 하거나 좋아하는 음악을 들어보세요."
        )

    def _generate_celebratory_response(self, text: str) -> str:
        """
        Generate a celebratory response when the user expresses positive sentiment.

        Args:
            text (str): Original user input.
        Returns:
            str: Celebratory response.
        """
        return (
            "좋은 소식이네요! 그렇게 긍정적인 경험을 나눠줘서 고마워요. 앞으로도 멋진 일들이 계속될 거예요. "
            "혹시 오늘 기분을 더 좋게 만들어줄 취미나 음식을 추천해 드릴까요?"
        )

    def _generate_neutral_response(self, text: str) -> str:
        """
        Generate a neutral response for general conversation.

        Args:
            text (str): Original user input.
        Returns:
            str: Neutral response.
        """
        # Offer to share daily life or provide recommendations
        return (
            "오늘 하루는 어떠셨나요? 같이 일상의 이야기를 나눠보거나, 새로운 취미와 맛집을 찾아보는 건 어떠세요?"
        )


# Example usage (command-line demo)
if __name__ == "__main__":
    agent = AIAgentFriend()
    print("AI Agent 친구와 대화를 시작합니다. 종료하려면 'exit'을 입력하세요.")
    while True:
        user_input = input("사용자: ")
        if user_input.lower().strip() == "exit":
            print("대화를 종료합니다. 좋은 하루 보내세요!")
            break
        if user_input.startswith("추천:"):
            # Extract preference after '추천:' prefix
            pref = user_input.split(":", 1)[-1].strip()
            response = agent.recommend_activity(pref)
        else:
            response = agent.handle_text(user_input)
        print("에이전트:", response)
