import { EventType, ResponseTier, ActionKind } from "../src/types.js";

describe("enums", () => {
  it("EventType values", () => {
    expect(EventType.Message).toBe("message");
    expect(EventType.Image).toBe("image");
    expect(EventType.FriendRequest).toBe("friend_request");
    expect(EventType.Gift).toBe("gift");
    expect(EventType.ProfileChange).toBe("profile_change");
    expect(EventType.VoiceClip).toBe("voice_clip");
  });

  it("ResponseTier values", () => {
    expect(ResponseTier.Trusted).toBe("trusted");
    expect(ResponseTier.Critical).toBe("critical");
  });

  it("ActionKind values", () => {
    expect(ActionKind.None).toBe("none");
    expect(ActionKind.MandatoryReport).toBe("mandatory_report");
  });
});
