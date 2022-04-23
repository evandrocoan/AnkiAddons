
jest.disableAutomock();
jest.setTimeout(100000);

describe("Template basic regex operations", () => {
    test(`Adding ruby furigana kanji with bold`, async function () {
        let mainfield = /(<ruby>.*彼.*?(?:<\/ruby>)|彼)/ig;
        let original = `<ruby><rb>彼</rb><rt>わたし</rt></ruby>は<ruby><rb>友達</rb><rt>になれた</rt></ruby>を<ruby><rb>便</rb><rt>っ</rt></ruby>つ<ruby><rb>持</rb><rt>も</rt></ruby>っだね。`;
        let expected = `<b><ruby><rb>彼</rb><rt>わたし</rt></ruby></b>は<ruby><rb>友達</rb><rt>になれた</rt></ruby>を<ruby><rb>便</rb><rt>っ</rt></ruby>つ<ruby><rb>持</rb><rt>も</rt></ruby>っだね。`;
        let newsentece = original.replace(mainfield, `<b>$1</b>`);
        expect(newsentece).toEqual(expected);
    });
});
